# -*- coding: utf-8 -*-
"""Customer_Churn_prediction_PAI.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1kKBVf7wlIVXCjZVAoM8Njx-C2_BcRDJt
"""

pip install catboost

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score, roc_curve,confusion_matrix

import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import cdist
import openpyxl  # Required to save results to Excel

"""#Dataset Loading"""

df = pd.read_excel('E Commerce Dataset.xlsx', sheet_name='E Comm')

"""Data Understanding"""

df.head()

df.tail()

print("Dataset shape:", df.shape)
df.info()
df.describe()

df.isnull().sum()

df['DaySinceLastOrder'].unique()

# Visualize Target Variable
sns.countplot(x='Churn', data=df,palette='rainbow')
plt.title("Target Variable Distribution")
plt.show()

"""Categorical Features

These are non-numeric or discrete features that represent categories:

PreferredLoginDevice
PreferredPaymentMode
Gender
PreferedOrderCat
MaritalStatus
"""

# Bar charts for categorical features
categorical_features = ['PreferredLoginDevice', 'PreferredPaymentMode',
                        'Gender', 'PreferedOrderCat', 'MaritalStatus']

for feature in categorical_features:
    plt.figure(figsize=(8, 5))
    churn_counts = df.groupby([feature, 'Churn']).size().reset_index(name='Count')
    sns.barplot(data=churn_counts, x=feature, y='Count', hue='Churn', palette='Set2')
    plt.title(f'Bar Chart of {feature} by Churn')
    plt.xlabel(feature)
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.legend(title='Churn', loc='upper right')
    plt.show()

# Identify features and target
target = "Churn"
features = df.drop(columns=[target])
labels = df[target]

numerical_features = ['Tenure', 'CityTier','WarehouseToHome', 'HourSpendOnApp',
                      'NumberOfDeviceRegistered','SatisfactionScore','NumberOfAddress','Complain',
                      'OrderAmountHikeFromlastYear', 'CouponUsed',
                      'OrderCount', 'DaySinceLastOrder', 'CashbackAmount']
for feature in numerical_features:
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x='Churn', y=feature, palette='Set2')
    plt.title(f'Boxplot of {feature} by Churn')
    plt.xlabel('Churn')
    plt.ylabel(feature)
    plt.show()

# Plot histograms for numerical features
for feature in numerical_features:
    plt.figure(figsize=(8, 5))
    sns.histplot(data=df, x=feature, kde=True, bins=30, color='blue')
    plt.title(f'Histogram of {feature}')
    plt.xlabel(feature)
    plt.ylabel('Frequency')
    plt.show()

# Select only numerical columns before calculating correlation
numerical_df = df.select_dtypes(include=['number'])

# Calculate the correlation matrix
correlation_matrix = numerical_df.corr()

# Continue with the rest of your code
plt.figure(figsize=(12, 8))
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
plt.title("Correlation Matrix", fontsize=16)
plt.show()

# Handle missing values and scaling
numerical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_features),
        ('cat', categorical_transformer, categorical_features),
        ('drop', 'drop', ['CustomerID', 'CityTier', 'WarehouseToHome',
                          'NumberOfDeviceRegistered', 'NumberOfAddress', 'HourSpendOnApp'])
    ]
)

# Function for clustering-based balancing
def balance_classes(X, y):
    """
    Use KMeans to cluster the majority class and select representative samples.
    """
    positive_class = X[y == 1]
    negative_class = X[y == 0]

    n_clusters = len(positive_class)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(negative_class)

    selected_indices = []
    for center in kmeans.cluster_centers_:
        distances = cdist([center], negative_class)
        closest_index = np.argmin(distances)
        selected_indices.append(closest_index)

    sampled_negative = negative_class[selected_indices]
    balanced_X = np.vstack((sampled_negative, positive_class))
    balanced_y = np.hstack((np.zeros(len(sampled_negative)), np.ones(len(positive_class))))
    return balanced_X, balanced_y

# Train models and evaluate
X_transformed = preprocessor.fit_transform(features)
X_train, X_test, y_train, y_test = train_test_split(
    X_transformed, labels, test_size=0.2, stratify=labels, random_state=42
)

balanced_X, balanced_y = balance_classes(X_train, y_train)

# Define models
models = [
    ("XGBoost", XGBClassifier(random_state=42)),
    ("CatBoost", CatBoostClassifier(random_state=42, verbose=0)),
    ("SVC", SVC(probability=True, random_state=42)),
    ("Logistic Regression", LogisticRegression(max_iter=1000, random_state=42)),
    ("Random Forest", RandomForestClassifier(random_state=42)),
    ("Gradient Boosting", GradientBoostingClassifier(random_state=42))
]

# Paper's results for Online Retail (provided manually as paper_results)
paper_results = {
    "Model": ["XGBoost", "CatBoost", "SVC", "Logistic Regression", "Random Forest", "Gradient Boosting"],
    "Balanced Accuracy": [0.93, 0.93, 0.73, 0.81, 0.92, 0.92],  # From paper (Online Retail)
    "F1-Score": [0.74, 0.74, 0.44, 0.56, 0.74, 0.74],  # From paper (Online Retail)
    "Precision": [0.91, 0.91, 0.73, 0.81, 0.92, 0.91],  # From paper (Online Retail)
    "Accuracy": [91.80, 91.80, 69.87, 81.75, 92.8, 92.8]  # From paper (Online Retail)
}

from sklearn.metrics import  balanced_accuracy_score
# Initialize an empty list to store the results
results = []

# Loop over each trained model
for model_name, model in models:
    # Train the model
    model.fit(balanced_X, balanced_y)

    # Predict using the trained model
    y_pred = model.predict(X_test)

    # Compute classification report (for accuracy, F1-score, precision, recall, etc.)
    report = classification_report(y_test, y_pred, output_dict=True)

    # Extract metrics for the positive class (class 1)
    f1_class_1 = report["1"]["f1-score"]
    precision_class_1 = report["1"]["precision"]

    # Compute balanced accuracy (average of sensitivity and specificity)
    balanced_acc = balanced_accuracy_score(y_test, y_pred)

    # Get accuracy from classification report (overall accuracy)
    accuracy = report["accuracy"]

    # Append the results to the list
    results.append({
        "Model": model_name,
        "Accuracy": accuracy,
        "F1-Score (Class 1)": f1_class_1,
        "Precision (Class 1)": precision_class_1,
        "Balanced Accuracy": balanced_acc
    })

# Convert the results into a DataFrame for comparison
results_df = pd.DataFrame(results)

# Convert paper results into DataFrame
paper_df = pd.DataFrame(paper_results)

# Merge the results with the paper results for comparison
comparison_df = pd.merge(results_df, paper_df, on="Model", suffixes=("_Model", "_Paper"))

# Display the comparison DataFrame
print(comparison_df)

# Optionally, save the comparison to a CSV file
comparison_df.to_csv('Model_vs_Paper_Comparison_Results.csv', index=False)

"""RUC and AUC curve"""

# Loop through each model to compute ROC and AUC
for model_name, model in models:
    # Predict probabilities for the positive class (class 1)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Compute ROC curve
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)

    # Compute AUC score
    auc = roc_auc_score(y_test, y_pred_proba)

    # Plot ROC curve
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.2f})')
    plt.plot([0, 1], [0, 1], linestyle='--', color='gray')  # Random model (diagonal)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curve for {model_name}')
    plt.legend(loc='lower right')
    plt.show()

    # Display AUC score
    print(f"{model_name} - AUC Score: {auc:.2f}")