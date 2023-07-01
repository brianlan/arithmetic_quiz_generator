import argparse
import datetime
from pathlib import Path
import json
import random
from loguru import logger

from src.helper import (
    NoValidExpressionFound,
    operator_combinations,
    is_valid_expression,
    is_integer_or_no_fraction,
    default_output_path,
    to_printable,
    generate_quiz_sheet_html_table,
)

parser = argparse.ArgumentParser()
parser.add_argument("--sheet-serial-number", type=int, required=True)
parser.add_argument("--sheet-date", type=str, required=True)
parser.add_argument("-c", "--configs", nargs="+", type=Path, required=True)
# parser.add_argument("-o", "--output-path", type=Path, default=default_output_path())


def generate_quiz(config, operator_combination, max_iterations=1e6):
    """
    Generates an arithmetic quiz based on the config and operator combination.
    Ensures that the intermediate results and final result are integers or floats with no fractional part,
    and within the specified range.

    :param config: The configuration dictionary for the quiz.
    :param operator_combination: The combination of operators to be used.
    :return: A tuple containing a string representing the quiz and the number of iterations it took to generate it.
    """

    operands_config = config["operands"]
    num_of_operands = len(operands_config)
    intermediate_result_range = config["intermediate_result_range"]
    final_result_range = config["final_result_range"]

    iteration_count = 0

    while True and iteration_count <= max_iterations:
        iteration_count += 1
        # Generate a list of operators and operands
        expression = []
        valid_expression = True

        for i in range(num_of_operands):
            # Generating an operand
            operand_min = operands_config[i]["min_value"]
            operand_max = operands_config[i]["max_value"]
            operand = random.randint(operand_min, operand_max)
            expression.append(str(operand))

            # Use the provided operator combination
            if i < num_of_operands - 1:
                expression.append(operator_combination[i])

                # Check for validity of intermediate expression if at least one operand and one operator are present
                if i > 0:
                    temp_expression = expression.copy()
                    # Check if the last element is an operator; if so, remove it for validity check
                    if temp_expression[-1] in operator_combination:
                        temp_expression.pop()
                    temp_result = eval("".join(temp_expression))
                    if not (
                        is_integer_or_no_fraction(temp_result)
                        and intermediate_result_range["min_value"]
                        <= temp_result
                        <= intermediate_result_range["max_value"]
                    ):
                        valid_expression = False
                        break

        # Check for validity of final expression if intermediate expression is valid
        if valid_expression:
            final_result = eval("".join(expression))
            if (
                is_integer_or_no_fraction(final_result)
                and final_result_range["min_value"]
                <= final_result
                <= final_result_range["max_value"]
            ):
                return " ".join(expression), iteration_count
    else:
        raise NoValidExpressionFound(
            f"No valid expression found within {max_iterations} iterations for operator combination {operator_combination}"
        )


def main(args):
    # Example usage
    logger.info(f"Number of quiz sets: {len(args.configs)}")
    quiz_sets = []
    for config_path in args.configs:
        with open(config_path, "r") as file:
            config = json.load(file)
        quiz_sets.append(generate_quiz_set(config))

    sheet_dates = [get_date_of_next_n_days(args.sheet_date, n=i) for i in range(len(quiz_sets))]
    sheet_serial_numbers = [args.sheet_serial_number + i for i in range(len(quiz_sets))]
    cur_time = f'{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")}'

    html_tables = []
    answer_sheets = []
    for quiz_set, sheet_date, sheet_serial_number in zip(quiz_sets, sheet_dates, sheet_serial_numbers):
        # output quiz answer sheets
        answer_sheet = "\n".join(quiz_set)
        answer_sheets.append(answer_sheet)
    
        # output quiz html sheet for printing
        html_table = generate_quiz_sheet_html_table(
            sheet_serial_number,
            sheet_date,
            [q.split("=")[0] + "=" for q in quiz_set],
        )
        html_tables.append(html_table)
    
    full_answer_sheet = "\n-------------------------------------------------\n".join(answer_sheets)
    output_quiz_answer_sheet(full_answer_sheet, Path('generated_quiz'), args.sheet_date, cur_time)

    full_html = create_full_html_from_html_tables(html_tables)
    output_quiz_html_sheet(full_html, Path('generated_quiz'), args.sheet_date, cur_time)


def generate_quiz_set(config, shuffle=True):
    generated_quizzes = []
    for i, req in enumerate(config["requirements"]):
        num_of_operators = len(req["operands"]) - 1
        combinations = operator_combinations(req["valid_operators"], num_of_operators)

        tmp_quizzes = set()
        while len(tmp_quizzes) < req["num_quizzes"]:
            operator_combination = random.choice(combinations)
            try:
                quiz, num_tried = generate_quiz(req, operator_combination)
                tmp_quizzes.add(to_printable(quiz))
            except NoValidExpressionFound as e:
                logger.warning(e)
        logger.info(
            f"Finished Generation of requirements {i}, {req['num_quizzes']} quizzes generated"
        )

        generated_quizzes.extend(tmp_quizzes)

    if shuffle:
        random.shuffle(generated_quizzes)

    return generated_quizzes


def output_quiz_answer_sheet(answer_sheet, out_dir: Path, sheet_date, cur_time):
    output_path = out_dir / sheet_date / f'{cur_time}.txt'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(answer_sheet)


def output_quiz_html_sheet(html, out_dir: Path, sheet_date, cur_time):
    output_path = out_dir / sheet_date / f'{cur_time}.html'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)


def get_date_of_next_n_days(cur_date, n=1):
    return (datetime.datetime.strptime(cur_date, "%Y-%m-%d") + datetime.timedelta(days=n)).strftime("%Y-%m-%d")


def create_full_html_from_html_tables(html_tables):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    </head>
    <body>
    """
    for table in html_tables:
        html += table + "<br>"
    html += """
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    main(parser.parse_args())
