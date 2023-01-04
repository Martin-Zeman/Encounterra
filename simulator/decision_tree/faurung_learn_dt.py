import pandas
from sklearn.tree import DecisionTreeClassifier
import pickle

df = pandas.read_csv("faurung_table.csv")

mapping = {'Firebolt': 0, 'Chaosbolt': 1, 'Haste': 2, 'Quickened Fireball': 3, 'Twinned Chaosbolt': 4, 'Twinned Firebolt': 5,
           'Twinned Haste': 6, 'Fireball': 7}
inv_mapping = {v: k for k, v in mapping.items()}
df['decision'] = df['decision'].map(mapping)

features = ['enemies', 'cast_leveled', 'ss1', 'ss2', 'ss3', 'enemy_adjacent', 'allies', 'is_concentrating', 'sorcery_points']

X = df[features]
y = df['decision']

dtree = DecisionTreeClassifier()
dtree = dtree.fit(X.values, y)

assert "Firebolt" == inv_mapping[dtree.predict([[3, True, 4, 3, 2, False, 0, False, 0]])[0]]
assert "Fireball" == inv_mapping[dtree.predict([[4, False, 4, 3, 2, False, 0, False, 0]])[0]]

with open('faurung_model.pickle', 'wb') as handle:
    pickle.dump(dtree, handle, protocol=pickle.HIGHEST_PROTOCOL)
