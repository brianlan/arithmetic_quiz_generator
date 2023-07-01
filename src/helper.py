from pathlib import Path
import itertools
import random
import datetime
from jinja2 import Template


class NoValidExpressionFound(Exception):
    pass


def get_day_of_week(sheet_date):
    # create a list of weekday names in Chinese (starting with Monday)
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    # get the integer representation of the weekday (where Monday is 0 and Sunday is 6)
    weekday_int = sheet_date.weekday()

    # get the Chinese name of the weekday by indexing into the list
    weekday_name = weekday_names[weekday_int]

    return weekday_name


def generate_quiz_sheet_html_table(sheet_serial_number, sheet_date, quizzes):
    """Generate HTML quiz sheet using Jinja2 template
    Requirements:
    1. split quizzes into 2 columns (roughly equal size), the first half is on the left, the second half is on the right
    2. 1 blank row between 2 quiz rows

    Parameters
    ----------
    quizzes : a list of quizzes, each quiz is a string like '6 + 2 ='
        _description_

    Returns
    -------
    str
        html string
    """
    template = Template(Path("templates/quiz_sheet.html").read_text())
    first_half = quizzes[: (len(quizzes) + 1) // 2]
    second_half = quizzes[(len(quizzes) + 1) // 2 :]
    quizzes_reorg = itertools.zip_longest(
        range(1, len(first_half) + 1),
        first_half,
        range(len(first_half) + 1, len(quizzes) + 1),
        second_half,
        fillvalue="&nbsp;",
    )
    sheet_date = datetime.datetime.strptime(sheet_date, "%Y-%m-%d")
    return template.render(
        date=sheet_date.strftime("%Y年%-m月%-d日"),
        dayofweek=get_day_of_week(sheet_date),
        sheet_serial_number=sheet_serial_number,
        quizzes=quizzes_reorg,
    )


def default_output_path():
    dt = datetime.datetime.now().strftime("%Y-%m-%d")
    dtm = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    return Path("generated_quiz") / dt / f"{dtm}.txt"


def to_printable(expr: str, max_operand_len: int = 3):
    num_operands = len(expr.split()[::2])
    fixed_width = max_operand_len * num_operands + (num_operands - 1) * 3
    printable_expr = (
        expr.replace("/", "÷").replace("*", "x")
        + " " * (fixed_width - len(expr))
        + " = "
        + f"{eval(expr):.0f}"
    )
    return printable_expr


def operator_combinations(valid_operators, num_of_operators):
    """
    Generate all the possible combinations of operators based on the probabilities.
    The combinations are shuffled.

    :param valid_operators: A dictionary containing operators and their probabilities.
    :param num_of_operators: The number of operators required in each combination.
    :return: A list containing tuples of shuffled operator combinations.
    """

    # Extract the operators and probabilities from the dictionary
    operator_choices = list(valid_operators.keys())
    operator_probabilities = [
        int(valid_operators[op]["probability"] * 100) for op in operator_choices
    ]

    # Expand the operator_choices based on probabilities
    expanded_operator_choices = [
        op
        for op, prob in zip(operator_choices, operator_probabilities)
        for _ in range(prob)
    ]

    # Generate all combinations of the operators
    combinations = list(
        itertools.product(expanded_operator_choices, repeat=num_of_operators)
    )

    # Shuffle the combinations
    random.shuffle(combinations)

    return combinations


def is_valid_expression(expression, intermediate_result_range):
    temp_expression = []
    for index, item in enumerate(expression):
        temp_expression.append(item)
        if index % 2 == 0 and index > 1:
            temp_result = eval("".join(temp_expression))
            if not (
                isinstance(temp_result, (int, float))
                and intermediate_result_range["min_value"]
                <= temp_result
                <= intermediate_result_range["max_value"]
            ):
                return False
            temp_expression = [str(temp_result)]
    return True


def is_integer_or_no_fraction(number):
    """
    Check if the number is an integer or a float with no fractional part.

    :param number: The number to check.
    :return: True if the number is an integer or a float with no fractional part, False otherwise.
    """
    return isinstance(number, int) or (
        isinstance(number, float) and number.is_integer()
    )
