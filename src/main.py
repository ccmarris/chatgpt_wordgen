#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main script to generate responses from ChatGPT for a set of prompts and save them to a Word document.
"""
__author__ = "Chris Marrison"
__copyright__ = "Copyright 2023, Chris Marrison / Infoblox"
__license__ = "BSD2"
__version__ = "0.1.0"
__email__ = "chris@infoblox.com"

import logging
import argparse
import chatgpt_client
import time
from prompts import PROMPTS
from docgen import save_responses_to_docx
from rich import print
from tqdm import tqdm

_logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ini", 
                        type=str, 
                        default="ai.ini", 
                        help="Path to the ini file with API key and model settings",
                        required= False)
    parser.add_argument(
        "-s", "--sleep",
        type=int,
        default=1,
        help="Sleep time in seconds between requests to avoid hitting rate limits (default: 1 second)")
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output.docx",
        help="Output filename (default: output.docx)")
    parser.add_argument(
        "-f", "--output-format",
        choices=["docx", "txt", "md", "stdout"],
        default="docx",
        help="Output format: docx (default), txt, md or stdout")
    parser.add_argument(
        "-p", "--prompt-file",
        type=str,
        help="Path to a file containing prompts (one per line). If not set, uses PROMPTS from prompts.py")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging")
    # Add arguments for custom weightings
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top_p", type=float, default=1.0)
    parser.add_argument("--frequency_penalty", type=float, default=0.0)
    parser.add_argument("--presence_penalty", type=float, default=0.0)
    args = parser.parse_args()
    return args


def setup_logging(debug):
    '''
     Set up logging

     Parameters:
        debug (bool): True or False.

     Returns:
        None.

    '''
    # Set debug level
    if debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s: %(message)s')
    return


def load_prompts(prompt_file=None):
    '''
    Load prompts from a file or use the default PROMPTS list.
    Parameters:
        prompt_file (str): Path to a file containing prompts (one per line). If None, uses the default PROMPTS.
    Returns:
        list: A list of prompts.
    '''
    prompts = []
    if prompt_file:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]
    else:
        prompts = PROMPTS
    return prompts


def save_responses(prompt_response_pairs, filename, output_format):
    '''
    Save the generated responses to a file in the specified format.
    Parameters:
        prompt_response_pairs (list): A list of tuples containing prompts and their corresponding responses.
        filename (str): The name of the output file.
        output_format (str): The format to save the responses in ("docx", "txt", or "md").
    Returns:
        None
    '''
    if output_format == "docx":
        _logger.info(f"Saving responses to {filename} in DOCX format")
        # Use the docgen module to save responses to a Word document
        save_responses_to_docx(prompt_response_pairs, filename=filename)
    elif output_format == "txt":
        _logger.info(f"Saving responses to {filename} in TXT format")
        # Save responses to a text file
        with open(filename, "w", encoding="utf-8") as f:
            for prompt, response in prompt_response_pairs:
                f.write(f"Prompt: {prompt}\nResponse: {response}\n\n")
    elif output_format == "md":
        _logger.info(f"Saving responses to {filename} in Markdown format")
        # Save responses to a Markdown file
        with open(filename, "w", encoding="utf-8") as f:
            for prompt, response in prompt_response_pairs:
                f.write(f"## Prompt\n{prompt}\n\n### Response\n{response}\n\n")
    elif output_format == "stdout":
        _logger.info("Printing responses to stdout")
        # Print responses to standard output
        for prompt, response in prompt_response_pairs:
            print(f"## Prompt: {prompt}\n## Response: {response}\n")
    else:
        _logger.error(f"Unknown output format: {output_format}")
    
    return


def main():
    # Example: custom weightings
    prompt_response_pairs:list = []
    args = parse_args()

    if args.temperature is not None:
        temperature = args.temperature
    if args.top_p is not None:
        top_p = args.top_p
    if args.frequency_penalty is not None:
        frequency_penalty = args.frequency_penalty
    if args.presence_penalty is not None:
        presence_penalty = args.presence_penalty
    
    setup_logging(debug=args.debug)  # Set debug to True for verbose logging

    _logger.debug(
        f"Using parameters: temperature={temperature}, top_p={top_p}, frequency_penalty={frequency_penalty}, presence_penalty={presence_penalty}"
    )

    # Load prompts
    prompts = load_prompts(args.prompt_file)

    # Initialize ChatGPT client
    client = chatgpt_client.ChatGPTClient(inifile=args.ini)

    # Generate responses for each prompt
    try:
        for prompt in tqdm(prompts, desc="Processing prompts"):
            _logger.info(f"Sending prompt: {prompt}")
            response = client.get_response(
                prompt,
                temperature=args.temperature,
                top_p=args.top_p,
                frequency_penalty=args.frequency_penalty,
                presence_penalty=args.presence_penalty,
            )
            if response == 'Success':
                prompt_response_pairs.append((prompt, client.last_response))
                time.sleep(args.sleep)
            else:
                _logger.error(f"Error generating response for prompt: {prompt}")
                _logger.error(f"Exiting due to error: {response}")
                print(f"[red]Error generating response for prompt: {prompt}[/red]")
                print(f"[red]Exiting due to error:[/red] {response}")
                break
    except KeyboardInterrupt:
        _logger.warning("Interrupted by user. Saving partial results...")

    if prompt_response_pairs:
        _logger.info(f"Saving responses to {args.output} (format: {args.output_format})")
        save_responses(prompt_response_pairs, filename=args.output, output_format=args.output_format)
    else:
        _logger.warning("No responses to save.")

    return

if __name__ == "__main__":
    main()