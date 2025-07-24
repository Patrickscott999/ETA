import streamlit as st
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# --- Galactic Soccer Theme Styling ---
st.set_page_config(
    page_title="⚽️ Galactic Soccer ETA Predictor",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Galactic Soccer theme
st.markdown(
    """
    <style>
    body {
        background: url('https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1200&q=80') no-repeat center center fixed;
        background-size: cover;
        color: #f8f8ff;
    }
    .stApp {
        background: rgba(15, 15, 40, 0.97);
    }
    .block-container {
        background: rgba(30, 40, 60, 0.96);
        border-radius: 1.5em;
        padding: 2em;
        box-shadow: 0 0 32px 8px #00ff99;
    }
    .stButton>button {
        color: #fff !important;
        background: linear-gradient(90deg, #00ff99, #4361ee 80%);
        border: none;
        border-radius: 20px;
        padding: 0.5em 2em;
        margin: 0.5em 0;
        font-weight: bold;
        letter-spacing: 1px;
        box-shadow: 0 0 10px #00ff99;
    }
    .stDownloadButton>button {
        color: #fff !important;
        background: linear-gradient(90deg, #00ff99, #7209b7 80%);
        border: none;
        border-radius: 20px;
        padding: 0.5em 2em;
        margin: 0.5em 0;
        font-weight: bold;
        letter-spacing: 1px;
        box-shadow: 0 0 10px #7209b7;
    }
    .stDataFrame {
        background: rgba(30, 60, 30, 0.95);
        color: #f8f8ff;
        border-radius: 1em;
    }
    h1, h2, h3, .stTitle {
        color: #00ff99 !important;
        text-shadow: 0 0 10px #7209b7;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar ---
st.sidebar.image(
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
    use_container_width=True,
)
st.sidebar.title("⚽️ Galactic Soccer ETA Predictor")
st.sidebar.markdown(
    """
    **Galactic Soccer Instructions:**
    - Upload your delivery CSV (with soccer stats or food orders from another planet!)
    - The app will predict the ETA (delivery time in minutes) for each order.
    - Download your results and see your galactic soccer stats! 🪐⚽️
    
    <span style='font-size:1.5em'>🌌 <b>Score big with cosmic delivery predictions!</b> 🌌</span>
    """,
    unsafe_allow_html=True
)

st.title("⚽️ Galactic Soccer Delivery ETA")
st.caption("Upload your delivery dataset and get instant ETA predictions with a soccer twist!")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

def feature_engineering(df):
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['actual_delivery_time'] = pd.to_datetime(df['actual_delivery_time'], errors='coerce')
    df['delivery_time_minutes'] = (df['actual_delivery_time'] - df['created_at']).dt.total_seconds() / 60
    df['order_hour'] = df['created_at'].dt.hour
    df['order_dayofweek'] = df['created_at'].dt.dayofweek
    df['store_primary_category'] = df['store_primary_category'].astype(str)
    return df

def build_model(X, y):
    numeric_features = [
        'estimated_store_to_consumer_driving_duration',
        'subtotal',
        'total_items',
        'order_hour',
        'order_dayofweek'
    ]
    categorical_features = ['store_primary_category']
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ]
    )
    model = Pipeline([
        ('pre', preprocessor),
        ('rf', RandomForestRegressor(n_estimators=20, random_state=42))  # Reduced for speed
    ])
    model.fit(X, y)
    return model

# --- Batch Prediction (CSV Upload) ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    if len(df) > 20000:
        st.warning(f"Large file detected ({len(df)} rows). Training and prediction may take longer.")
    df = feature_engineering(df)
    st.write("Preview of uploaded data:", df.head())

    required_cols = [
        'estimated_store_to_consumer_driving_duration',
        'subtotal',
        'total_items',
        'order_hour',
        'order_dayofweek',
        'store_primary_category'
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing columns in your data: {missing_cols}")
    else:
        with st.spinner('Training or loading model and making predictions...'):
            if 'delivery_time_minutes' in df.columns and df['delivery_time_minutes'].notnull().any():
                # SAMPLE for training if large
                if len(df) > 10000:
                    st.info(f"Training on a random sample of 10,000 rows out of {len(df)} for speed.")
                    train_df = df.sample(n=10000, random_state=42)
                else:
                    train_df = df
                X = train_df[required_cols]
                y = train_df['delivery_time_minutes']
                model = build_model(X, y)
                joblib.dump(model, 'delivery_time_advanced_model.pkl')
                st.success("Model trained on your uploaded data and saved for future predictions.")
            else:
                try:
                    model = joblib.load('delivery_time_advanced_model.pkl')
                    st.info("Using pre-trained model for prediction.")
                except Exception as e:
                    st.error("No target column found and no pre-trained model available.")
                    st.stop()
            preds = model.predict(df[required_cols])
        df['Predicted_Delivery_Time_Minutes'] = preds
        st.write("Prediction Results:", df[['Predicted_Delivery_Time_Minutes']].head())
        st.download_button(
            label="Download results as CSV",
            data=df.to_csv(index=False),
            file_name="delivery_eta_predictions.csv",
            mime="text/csv"
        )
        st.subheader("Predicted Delivery Time Distribution")
        st.bar_chart(df['Predicted_Delivery_Time_Minutes'])

# --- Single Order ETA Prediction ---
st.markdown("---")
st.header("🌠 Predict ETA for a Single Order")
with st.form("single_order_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        est_drive = st.number_input("Estimated store-to-consumer driving duration (seconds)", min_value=0, value=600)
        subtotal = st.number_input("Order subtotal (cents)", min_value=0, value=2500)
    with col2:
        total_items = st.number_input("Total items", min_value=1, value=3)
        order_hour = st.slider("Order hour (0-23)", 0, 23, 12)
    with col3:
        order_dayofweek = st.selectbox("Day of week", options=[0,1,2,3,4,5,6], format_func=lambda x: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][x])
        store_primary_category = st.text_input("Store primary category", value="4")
    submitted = st.form_submit_button("Predict ETA 🚀")

if submitted:
    # Try to load model, fallback to error
    with st.spinner('Predicting ETA...'):
        try:
            model = joblib.load('delivery_time_advanced_model.pkl')
        except Exception:
            st.error("Pre-trained model not found. Please upload a CSV with delivery times to train a model first.")
            st.stop()
        input_df = pd.DataFrame({
            'estimated_store_to_consumer_driving_duration': [est_drive],
            'subtotal': [subtotal],
            'total_items': [total_items],
            'order_hour': [order_hour],
            'order_dayofweek': [order_dayofweek],
            'store_primary_category': [store_primary_category]
        })
        eta_pred = model.predict(input_df)[0]
    st.success(f"Predicted Delivery ETA: {eta_pred:.1f} minutes 🛸")

st.markdown("---")
st.markdown("**Instructions:** Upload a CSV with at least the following columns: `created_at`, `store_primary_category`, `estimated_store_to_consumer_driving_duration`, `subtotal`, `total_items`." )
