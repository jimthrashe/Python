import pandas as pd

# Load csv into dataframe

df = pd.read_csv('sniepit.csv')


# Display first few rows of DF to make sure worked

#print(df.head())

def replace_spaces():
    """
    replaces spaces with underscores in all columns of a dataframe.
    """
    return df.replace(' ', '_', regex=True)

#Tuples to select

replacein = ['Model No.','Asset Name']

for column in replacein:

    df[column] = df[column].replace('example', 'example2', regex=True)




