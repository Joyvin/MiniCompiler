import llvmlite.ir as ir # type: ignore
import llvmlite.binding as llvm # type: ignore
import ast
import subprocess
import sys

# Initialize LLVM
llvm.initialize()
llvm.initialize_native_target()
llvm.initialize_native_asmprinter()

class LLVMCompiler(ast.NodeVisitor):
    def __init__(self):
        self.module = ir.Module(name="main")
        self.functions = {}
        self.builder = None
        self.local_symbols = {}
        self.string_constants = {}  # Store unique string constants
        self.declare_printf()

    def compile(self, source_code):
        tree = ast.parse(source_code)
        for stmt in tree.body:
            if isinstance(stmt, ast.FunctionDef):
                self.declare_function(stmt)

        for stmt in tree.body:
            self.visit(stmt)

        self.module.triple = llvm.get_default_triple()
        target = llvm.Target.from_default_triple().create_target_machine()
        self.module.data_layout = target.target_data

        return str(self.module)

    def declare_printf(self):
        """Declares printf function for printing."""
        printf_type = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf = ir.Function(self.module, printf_type, name="printf")

    def create_string_constant(self, text):
        """Creates and reuses unique string constants."""
        if text in self.string_constants:
            return self.string_constants[text]

        string_bytes = bytearray(text + "\0", "utf8")
        str_type = ir.ArrayType(ir.IntType(8), len(string_bytes))
        string_var = ir.GlobalVariable(self.module, str_type, name=f"str_const_{len(self.string_constants)}")
        string_var.linkage = "internal"
        string_var.global_constant = True
        string_var.initializer = ir.Constant(str_type, string_bytes)

        self.string_constants[text] = self.builder.bitcast(string_var, ir.PointerType(ir.IntType(8)))
        return self.string_constants[text]

    def declare_function(self, node):
        param_types = [ir.IntType(32)] * len(node.args.args)
        func_type = ir.FunctionType(ir.IntType(32), param_types)
        func = ir.Function(self.module, func_type, name=node.name)
        self.functions[node.name] = func

    def visit_FunctionDef(self, node):
        func = self.functions[node.name]
        block = func.append_basic_block("entry")
        self.builder = ir.IRBuilder(block)

        self.local_symbols = {arg.arg: func.args[i] for i, arg in enumerate(node.args.args)}
        for stmt in node.body:
            self.visit(stmt)

        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.IntType(32), 0))

    def visit_While(self, node):
        func = self.builder.function

        while_cond = func.append_basic_block("while_cond")
        while_body = func.append_basic_block("while_body")
        while_end = func.append_basic_block("while_end")

        self.builder.branch(while_cond)
        self.builder.position_at_end(while_cond)

        cond = self.visit(node.test)
        self.builder.cbranch(cond, while_body, while_end)

        self.builder.position_at_end(while_body)
        for stmt in node.body:
            self.visit(stmt)

        self.builder.branch(while_cond)
        self.builder.position_at_end(while_end)

    def visit_Return(self, node):
        if not self.builder.block.is_terminated:
            self.builder.ret(self.visit(node.value))

    def visit_Assign(self, node):
        var_name = node.targets[0].id
        value = self.visit(node.value)
        if var_name not in self.local_symbols:
            ptr = self.builder.alloca(value.type, name=var_name)
            self.local_symbols[var_name] = ptr
        else:
            ptr = self.local_symbols[var_name]
        self.builder.store(value, ptr)

    def visit_Name(self, node):
        if node.id in self.local_symbols:
            ptr = self.local_symbols[node.id]
            return self.builder.load(ptr, name=node.id) if isinstance(ptr.type, ir.PointerType) else ptr
        raise NameError(f"Undefined variable {node.id}")

    def visit_Expr(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.functions:
                return self.builder.call(self.functions[func_name], [self.visit(arg) for arg in node.args])
            elif func_name == "print":
                return self.handle_print(node.args)
        raise NotImplementedError(f"Function {node.func.id} not supported")

    def visit_Constant(self, node):
        if isinstance(node.value, int):
            return ir.Constant(ir.IntType(32), node.value)
        raise NotImplementedError(f"Constant type {type(node.value)} not supported")

    def visit_BinOp(self, node):
        lhs, rhs = self.visit(node.left), self.visit(node.right)
        ops = {ast.Add: self.builder.add, ast.Sub: self.builder.sub, 
               ast.Mult: self.builder.mul, ast.Div: self.builder.sdiv}
        return ops[type(node.op)](lhs, rhs, "binop") if type(node.op) in ops else None

    def visit_Compare(self, node):
        lhs, rhs = self.visit(node.left), self.visit(node.comparators[0])
        ops = {ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>=', ast.Eq: '=='}
        return self.builder.icmp_signed(ops[type(node.ops[0])], lhs, rhs, "cmp") if type(node.ops[0]) in ops else None

    def visit_BoolOp(self, node):
        """Handles logical operations (and, or)."""
        if isinstance(node.op, ast.And):
            return self.builder.and_(self.visit(node.values[0]), self.visit(node.values[1]), "andtmp")
        elif isinstance(node.op, ast.Or):
            return self.builder.or_(self.visit(node.values[0]), self.visit(node.values[1]), "ortmp")
        raise NotImplementedError(f"Boolean operator {type(node.op)} not supported")

    def visit_UnaryOp(self, node):
        """Handles 'not' logical operation."""
        if isinstance(node.op, ast.Not):
            value = self.visit(node.operand)
            return self.builder.icmp_signed('==', value, ir.Constant(ir.IntType(1), 0), "nottmp")
        raise NotImplementedError(f"Unary operator {type(node.op)} not supported")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mini_compiler.py <source_file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        source_code = f.read()

    compiler = LLVMCompiler()
    llvm_ir = compiler.compile(source_code)
    print("Out File Generated Successfully")
