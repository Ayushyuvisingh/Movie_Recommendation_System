
# 📽️ Movie Recommendation System

A **Movie Recommendation System** built with Python that recommends similar movies based on content similarity. The application uses pre-computed similarity scores for fast and accurate recommendations and is deployed as a web app for public access.

🔗 **Live Demo:** https://movie-recommendation-system-uvchyhjltnol2me8ggzjua.streamlit.app/

---

## 🚀 Project Overview

This project allows users to select a movie and instantly receive recommendations for similar movies. It demonstrates a **content-based filtering approach** using machine learning techniques to measure similarity between movies based on their metadata.

The system is optimized for performance by loading pre-trained similarity matrices instead of recomputing them every time.

---

## 🌐 Live Web Application

Try the project here (no installation required):

➡️ **https://movie-recommendation-system-uvchyhjltnol2me8ggzjua.streamlit.app/**

---

## 📂 Project Structure

```

Movie_Recommendation_System/
├── app.py                 # Main application file
├── movie_dict.pkl         # Serialized movie data
├── similarity.pkl         # Serialized similarity matrix
├── requirements.txt       # Project dependencies
├── Procfile               # Deployment configuration
├── runtime.txt            # Python runtime version
├── .gitignore
└── README.md              # Project documentation

````

---

## 🧠 Features

✔ Content-based movie recommendation  
✔ Fast inference using pre-computed similarity  
✔ Clean and simple web interface  
✔ Deployed online using Streamlit  
✔ Beginner-friendly and scalable project structure  

---

## 🛠️ Tech Stack

- **Python**
- **Pandas**
- **Scikit-learn**
- **Pickle**
- **Streamlit** 


---

## ⚙️ How It Works

1. Movie metadata is vectorized using techniques like **TF-IDF**.
2. **Cosine similarity** is computed between all movie vectors.
3. Similarity scores are stored as a pickle file.
4. When a user selects a movie, the system:
   - Finds the closest movies based on similarity
   - Returns the top recommended results instantly

---

## 🧪 Local Setup & Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Ayushyuvisingh/Movie_Recommendation_System.git
cd Movie_Recommendation_System
````

### 2️⃣ Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application Locally

```bash
python app.py
```

Open the browser and navigate to the local server URL shown in the terminal.

---

## 📈 Future Enhancements

* Add movie posters using TMDb API
* Implement collaborative filtering
* User login and watch-history tracking
* Deploy using Docker
* Improve UI/UX

