# budgiebot
Wikipedia bot to add JIPA citations to language articles


## Installation

Using miniconda3 - the following need to be done once.

1. Clone this repository
    ```bash
    git clone https://github.com/richardbeare/budgiebot.git
    ```
1. Change to the budgiebot folder
    ```bash
    cd budgiebot
    ```
1. Create a miniconda environment for budgiebot
    ```bash
    conda conda create -y -c conda-forge --name BudgieBot python=3.9 pandas
    ```
1. Activate the environment
    ```bash
    conda activate BudgieBot
    ```
1. Install dependencies with pip
    ```bash
    pip install -r requirements.txt
    ```
## Configuration

These steps also only need to be done once. The following is supposed to save
user details and passwords in config files for pywikibot to access. Carry out in
the same folder as above, with the BudgieBot environment activated.

```bash
pwb generate_user_files
```

On my configuration it reports not finding the script, but then offers a choice
from a menu - choose the number corresponding to generate_user_files then follow
the prompts. I don't have the appropriate accounts to test this.

## Running

Change to the appropriate folder and activate the environment
    
```bash
cd budgiebot
conda activate BudgieBot
pwb ./budgiebot.py -isoexcel:ipa_iso_edited.xlsx -site:wikipedia:en -dryrun -summary:'Adding JIPA citation to Further Reading'
```

In theory there are a lot of predefined flags, like -user:username that you can use. I'm not clear on how these interact with the 
config files created above.

Also, I haven't got propper commandline argument handling - `-isoexcel` is required but it isn't
enforced.

The `-isoexcel` references the spreadsheet containing the data. Headings must match those in our
preliminary discussions. The bot will filter out empty entries + (ENGLISH, SPANISH, FRENCH, GERMAN), but
doesn't deal with other errors properly (e.g. the cmn? and entries with two choices separated by / will
cause problems as I haven't figured out how to do propper exception handling)

The `-dryrun` option will loop through all cases displaying the diffs but not change anything.

There is a `-simulate` option that apparently tests the entire connection procedure without
submitting changes.

The `-interactive` option will display the diffs in text form and prompt the user as to
whether the changes should be submitted.