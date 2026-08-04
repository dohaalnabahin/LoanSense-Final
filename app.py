from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import joblib
import pandas as pd
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
import os

app = FastAPI()
os.makedirs("uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

model = joblib.load("loan_approval_model.pkl")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html"
    )


@app.get("/prediction")
def prediction(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="prediction.html"
    )


@app.post("/predict")
def predict(
    request: Request,
    Gender: str = Form(...),
    Married: str = Form(...),
    Dependents: str = Form(...),
    Education: str = Form(...),
    Self_Employed: str = Form(...),
    ApplicantIncome: float = Form(...),
    CoapplicantIncome: float = Form(...),
    LoanAmount: float = Form(...),
    Loan_Amount_Term: float = Form(...),
    Credit_History: float = Form(...),
    Property_Area: str = Form(...)
):
    data = pd.DataFrame({
        "Gender": [Gender],
        "Married": [Married],
        "Dependents": [Dependents],
        "Education": [Education],
        "Self_Employed": [Self_Employed],
        "ApplicantIncome": [ApplicantIncome],
        "CoapplicantIncome": [CoapplicantIncome],
        "LoanAmount": [LoanAmount],
        "Loan_Amount_Term": [Loan_Amount_Term],
        "Credit_History": [Credit_History],
        "Property_Area": [Property_Area]
    })

    # =========================
    # Feature Engineering
    # =========================
    data["TotalIncome"] = (
        data["ApplicantIncome"] +
        data["CoapplicantIncome"]
    )

    data["MonthlyLoanPayment"] = (
        data["LoanAmount"] /
        data["Loan_Amount_Term"]
    )

    data["LoanIncomeRatio"] = (
        data["LoanAmount"] /
        data["TotalIncome"]
    )

    prediction_result = model.predict(data)[0]

    probability = model.predict_proba(data)[0]

    confidence = round(max(probability) * 100, 2)

    if prediction_result == 1:
        result = "Approved"
        status = "approved"
    else:
        result = "Rejected"
        status = "rejected"

    # =========================
    # Recommendations
    # =========================
    if result == "Approved":
        recommendations = [
            "Your application satisfies the model requirements.",
            "Review the loan agreement carefully before signing.",
            "Ensure all submitted documents are accurate and complete.",
            "Maintain a good credit history for future financial opportunities."
        ]
    else:
        recommendations = [
            "Improve your credit history before applying again.",
            "Consider reducing the requested loan amount.",
            "Increase your total income if possible.",
            "Applying with a co-applicant may improve approval chances."
        ]

    return templates.TemplateResponse(
        request=request,
        name="prediction.html",
        context={
            "result": result,
            "confidence": confidence,
            "recommendations": recommendations
        }
    )


@app.get("/performance")
def performance(request: Request):

    metrics = {
        "accuracy": 89.43,
        "precision": 90.00,
        "recall": 95.29,
        "f1": 92.57,
        "roc": 88.72
    }

    models = [

        {
            "name": "Logistic Regression",
            "accuracy": 83.74,
            "precision": 89.16,
            "recall": 87.06,
            "f1": 88.10,
            "roc": 87.72
        },

        {
            "name": "Decision Tree",
            "accuracy": 73.17,
            "precision": 87.14,
            "recall": 71.76,
            "f1": 78.71,
            "roc": 74.01
        },

        {
            "name": "Random Forest",
            "accuracy": 86.18,
            "precision": 89.89,
            "recall": 89.41,
            "f1": 89.65,
            "roc": 88.53
        },

        {
            "name": "KNN ⭐",
            "accuracy": 89.43,
            "precision": 90.00,
            "recall": 95.29,
            "f1": 92.57,
            "roc": 88.72
        }

    ]

    return templates.TemplateResponse(
        request=request,
        name="performance.html",
        context={
            "metrics": metrics,
            "models": models
        }
    )


@app.get("/batch")
def batch(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="batch.html"
    )


@app.post("/batch_predict")
async def batch_predict(
    request: Request,
    file: UploadFile = File(...)
):

    # اسم الملف
    file_path = os.path.join("uploads", file.filename)

    # حفظ الملف
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # قراءة الملف
    if file.filename.endswith(".csv"):

        df = pd.read_csv(file_path)

    else:

        df = pd.read_excel(file_path)

    # =========================
    # Feature Engineering
    # =========================
    df["TotalIncome"] = (
        df["ApplicantIncome"] +
        df["CoapplicantIncome"]
    )
    df["MonthlyLoanPayment"] = (
        df["LoanAmount"] /
        df["Loan_Amount_Term"]
    )
    df["LoanIncomeRatio"] = (
        df["LoanAmount"] /
        df["TotalIncome"]
    )

    # =========================
    # Prediction
    # =========================
    prediction = model.predict(df)
    probability = model.predict_proba(df)

    df["Prediction"] = [
        "Approved"
        if p == 1
        else
        "Rejected"
        for p in prediction
    ]

    df["Confidence"] = (
        probability.max(axis=1) * 100
    ).round(2)

    # =========================
    # Save Results
    # =========================
    output_file = "loan_predictions.xlsx"
    output_path = os.path.join(
        "results",
        output_file
    )
    df.to_excel(
        output_path,
        index=False
    )

    return templates.TemplateResponse(
        request=request,
        name="batch.html",
        context={
            "filename": output_file,
            "rows": len(df)
        }
    )


@app.get("/about")
def about(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="about.html"
    )
    
@app.get("/documentation")
def documentation(request: Request):

    return templates.TemplateResponse(

        request=request,

        name="documentation.html"

    )    