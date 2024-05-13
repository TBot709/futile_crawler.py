import requests
import random
import time
import os
from datetime import datetime

'''
futile subdirectory url crawler

A script that crawls for valid subdirectory urls on domains that
have randomly generated content urls. You likely won't find a valid one, but
perhaps you want to try anyway, see if you're lucky.

Replace base url and other config values as wanted,
this script was tested on [REDACTED].com which has sub directory strings
formatted as shown in the example odds below.

EXAMPLE ODDS:

example.com/XXXXXX,
X one of [a-z][0-9]

36 potential characters, 6 characters in an id string =
2,176,782,336 potential strings.

21,767,824 to reach 1% chance of a random string being a hit.
If trying 1 id per second, 86,400 seconds in a day, we have to
run continuously for 252 days for a 1% change of finding a video.

Given an estimate for chance of winning the lottery, 1 out of 14 million,
the number of random strings to try for equivalent chance is 156.

Granted that we don't re-attempt urls between runs, chances will become
insignificatly better each run.

The 'prv-attmpts' text file that keeps a record of previoulsy attempted strings
is retrieved in full at the start of each run, but only appeneded to at the end
of each run. This helps when running multiple instances of this script in
the same directory, or when updating the 'prv-attempts' manually, even while
the script is running.

Note that having multiple instances of the script running, or reducing the
time between attempts (FREQUENCY_LIMIT), will increase the chance the target
domain will throttle or block your connections, depending on how they monitor
and limit their traffic.
'''

# # # # CONFIG
BASE_URL = "https://example.com/"
URL_GENERATION_CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"
NUM_CHARACTERS = 6

BASE_URL_SHORT_FOR_OUTPUT_FILES = \
        BASE_URL[(BASE_URL.find('//') + 2):BASE_URL.find('.')]

# each run makes NUM_ATTEMPTS attempts, with the urls tried so far
#  being backed up to a file after each run, so interuptions only result in
#  the url record of the current run being lost.
NUM_RUNS = 1000
NUM_ATTEMPTS = 156

# take care adjusting the frequency limit, going too low will likely
#  result in your connections being throttled or blocked by the domain
FREQUENCY_LIMIT = 1  # 1 second, 1000 milliseconds

# the following strings filter urls that return a 200, but are otherwise
#  unacceptable as a 'valid' url, false positives, etc.
UNACCEPTABLE_STRINGS = [
        "This video isn't available",
]

# # # # CONSTANTS
NUM_POSSIBILITIES = pow(len(URL_GENERATION_CHARACTERS), NUM_CHARACTERS)
PREVIOUS_ATTEMPTS_FILE = \
        "futile-crwl-prv-attmpts-" + BASE_URL_SHORT_FOR_OUTPUT_FILES + ".txt"
VALID_URL_FILENAME_PREFIX = \
        "futile-crwl-valid-urls-" + BASE_URL_SHORT_FOR_OUTPUT_FILES


def generate_random_string():
    characters = URL_GENERATION_CHARACTERS
    return "".join(random.choice(characters) for _ in range(NUM_CHARACTERS))


def check_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            for s in UNACCEPTABLE_STRINGS:
                if s in response.text:
                    print(f"\tvalid url, but was unacceptable as response contained \"{s}\": {url}")
                    return False
            return True
    except requests.RequestException:
        return False


def run(run_count):
    valid_urls = set()
    attempted_strings = set()
    previous_attempted_strings = set()

    if os.path.exists(PREVIOUS_ATTEMPTS_FILE):
        with open(PREVIOUS_ATTEMPTS_FILE) as f:
            for line in f.readlines():
                previous_attempted_strings.add(line.replace('\n', ''))

    chance_of_hit = (
            (100 * NUM_ATTEMPTS) /
            (NUM_POSSIBILITIES - len(previous_attempted_strings)))
    s_chance_of_hit = f"{chance_of_hit:.11f}".rstrip("0").rstrip(".") + "%"
    print(f"# RUN {run_count} STARTING, CHANCE OF FINDING VALID URL THIS RUN IS {s_chance_of_hit}.")

    attempts = 0
    random_string_attempts = 0
    while attempts < NUM_ATTEMPTS:
        random_string_attempts += 1
        random_string = generate_random_string()
        if random_string_attempts > 1000:
            print("!!!Too many attempts to generate random string!!!")
            break
        if random_string not in attempted_strings and \
                random_string not in previous_attempted_strings:
            attempts += 1
            random_string_attempts = 0
            attempted_strings.add(random_string)
            url = BASE_URL + random_string
            print(f"Testing {url}, {len(valid_urls)} valid urls found so far, attempt {attempts} out of {NUM_ATTEMPTS}, run {run_count}")
            if check_url(url):
                valid_urls.add(url)
                print(f"\tValid URL: {url}")
            time.sleep(FREQUENCY_LIMIT)

    if len(valid_urls) > 0:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"{VALID_URL_FILENAME_PREFIX}_{timestamp}.txt"
        print(f"# FOUND {len(valid_urls)} VALID URLS ON RUN {run_count}! SAVING TO {output_file}.")
        with open(output_file, "w") as f:
            for url in valid_urls:
                f.write(url + "\n")
    else:
        print(f"# NO VALID URLS FOUND ON RUN {run_count}.")

    with open(PREVIOUS_ATTEMPTS_FILE, "a") as f:
        f.writelines(list(map(lambda s: s + '\n', attempted_strings)))


def main():
    run_count = 0
    for _ in range(NUM_RUNS):
        run_count += 1
        run(run_count)


if __name__ == "__main__":
    main()
