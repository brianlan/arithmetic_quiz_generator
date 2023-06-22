import argparse
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
    generate_quiz_sheet,
)

parser = argparse.ArgumentParser()
parser.add_argument("--sheet-serial-number", type=int, required=True)
parser.add_argument("--sheet-date", type=str, required=True)
parser.add_argument("-c", "--config", type=Path, required=True)
parser.add_argument("-o", "--output-path", type=Path, default=default_output_path())


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
    config_path = args.config
    with open(config_path, "r") as file:
        config = json.load(file)

    generated_quizzes = []
    for i, req in enumerate(config["requirements"]):
        num_of_operators = len(req["operands"]) - 1
        combinations = operator_combinations(req["valid_operators"], num_of_operators)

        for operator_combination in combinations[: req["num_quizzes"]]:
            try:
                quiz, num_tried = generate_quiz(req, operator_combination)
                generated_quizzes.append(to_printable(quiz))
            except NoValidExpressionFound as e:
                print(e)
        logger.info(
            f"Finished Generation of requirements {i}, {req['num_quizzes']} quizzes generated"
        )

    random.shuffle(generated_quizzes)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(args.output_path, "w") as f:
        f.write("\n".join(generated_quizzes))

    # save html quiz sheet
    # the save path is the same as the output path, but with a .html extension
    with open(args.output_path.with_suffix(".html"), "w") as f:
        f.write(
            generate_quiz_sheet(
                args.sheet_serial_number, args.sheet_date, generated_quizzes
            )
        )


if __name__ == "__main__":
    main(parser.parse_args())
