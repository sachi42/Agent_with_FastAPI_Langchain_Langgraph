import ast
import operator

# Strict map of allowed operators to safely prevent arbitrary remote code execution
ALLOWED_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.USub: operator.neg, ast.UAdd: operator.pos
}

def calculate_expression(expression: str) -> str:
    cleaned = expression.replace("$", "").replace(",", "").strip()
    try:
        tree = ast.parse(cleaned, mode='eval')
        
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Num):  # Fallback compatibility
                return node.n
            elif isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                op_type = type(node.op)
                if op_type not in ALLOWED_OPERATORS:
                    raise TypeError(f"Unsupported mathematical operator: {op_type.__name__}")
                return ALLOWED_OPERATORS[op_type](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = _eval(node.operand)
                op_type = type(node.op)
                if op_type not in ALLOWED_OPERATORS:
                    raise TypeError(f"Unsupported unary operator: {op_type.__name__}")
                return ALLOWED_OPERATORS[op_type](operand)
            else:
                raise TypeError(f"Unsupported structure: {type(node).__name__}")
                
        result = _eval(tree)
        return f"Calculation Result: {result}"
    except Exception as e:
        return f"CALCULATION_ERROR: Invalid or unsafe expression provided. Details: {str(e)}"
