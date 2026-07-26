# Personalized Project-Based Learning Platform

## 📖 Overview

Is a web-based learning platform designed to help students and aspiring developers discover, learn, and complete real-world projects based on their interests, skills, and career goals. The platform provides personalized project recommendations, structured learning workflows, curated learning resources, and premium features to enhance the learning experience.

---

## ✨ Features

### 🎯 Personalized Recommendations

* Generates project recommendations based on user profiles, interests, and skill levels.
* Supports different recommendation limits for free and premium users.
* Refreshes recommendations using session-based tracking to maintain relevance.

### 🚀 Project Learning Workspace

* Allows users to start recommended or showcase projects.
* Provides a structured workflow divided into phases and tasks.
* Tracks progress through interactive checklists.
* Guides users through projects based on their profile and learning style.

### 📚 Project Discovery

* Dedicated Project Library for exploring projects.
* Projects categorized into:

  * Artificial Intelligence (AI)
  * Web Development
  * Data Science
  * Mobile Development
  * Cloud & DevOps
  * Cybersecurity
* Easy project enrollment through a "Start Project" workflow.
* Save, manage, and remove projects through the My Projects section.

### 🔗 Learning Resources

* Dedicated Resources page with curated learning materials.
* Resources organized by career paths and technical roles:

  * Frontend Development
  * Backend Development
  * Data Science
  * Cloud Computing
  * Cybersecurity
  * And more

### 💎 Plans & Premium Features

* Pricing plans displayed on the home page.
* Premium access request and status tracking.
* Feature access controlled based on user subscription plans.

### 🎨 Modern User Experience

* Responsive design for desktop, tablet, and mobile devices.
* Consistent and user-friendly navigation.
* Light/Dark theme support.
* Smooth authentication experience using modal-based interactions.

---

## 📁 Project Structure

```text
PBLR_system/
│
├── config/              # Main Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── users/               # User management and authentication
│
├── data/                # Project, recommendation, and learning-related features
│
├── media/               # Uploaded media files
│
├── db.sqlite3           # SQLite database
│
├── manage.py            # Django management script
│
└── README.md            # Project documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites

Make sure the following are installed on your system:

* Python 3.10+
* pip
* Git

### Clone the Repository

```bash
git clone https://github.com/your-username/PBLR_system.git
cd PBLR_system
```

### Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Run the Development Server

```bash
python manage.py runserver
```

### Access the Application

Open your browser and visit:

```text
http://127.0.0.1:8000/
```

---

## 🎯 Project Goal

The primary goal of SmartLearn is to bridge the gap between learning and practical experience by providing personalized, project-based learning opportunities that help users build real-world skills and portfolios.

---

## 👥 Target Users

* University Students
* Self-Learners
* Beginner Developers
* Career Switchers
* Technology Enthusiasts

---

## 🚀 Future Enhancements

* AI-powered recommendation engine
* Project collaboration features
* Community discussions and forums
* Certificates and achievement badges
* Advanced analytics and learning insights

---

## 📄 License

This project is developed for educational and learning purposes.
