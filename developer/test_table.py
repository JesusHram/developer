import pandas as pd
import reflex as rx

nba_data = pd.read_csv(
    "https://media.geeksforgeeks.org/wp-content/uploads/nba.csv"
)
...

def test_table():
    return rx.data_table(
    data=nba_data[["Name", "Height", "Age"]],
    pagination=True,
    search=True,
    sort=True,
)
