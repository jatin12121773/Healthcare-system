import pandas as pd
symptoms_df = pd.read_csv("dataset.csv")
# precautions_df = pd.read_csv("disease_dataset.csv")

symptoms_df.columns = [col.strip().lower() for col in symptoms_df.columns]
# precaution_df.columns = [col.strip().lower() for col in precautions_df.columns]

# Extract unique symptoms
all_symptoms = []
for col in symptoms_df.columns[1:]:
    for symptom in symptoms_df[col].dropna():
        if symptom not in all_symptoms:
            all_symptoms.append(symptom)
all_symptoms.sort()

print(len(all_symptoms))
# # symptoms_df.columns = [col.strip().lower() for col in symptoms_df.columns]
# print(all_symptoms)