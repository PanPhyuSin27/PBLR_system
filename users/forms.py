from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Plan, Project, UserProfile


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["field"].widget.attrs.update({"placeholder": "e.g. Data Science"})
        self.fields["target_role"].widget.attrs.update({"placeholder": "e.g. Data Analyst"})
        self.fields["tech_preference"].widget.attrs.update({"placeholder": "e.g. Python, SQL, Power BI"})
        self.fields["learning_goal"].widget.attrs.update({"placeholder": "e.g. Skill Improvement"})
        self.fields["interest_tags"].widget.attrs.update({"placeholder": "e.g. E-commerce, Finance, Healthcare"})

    class Meta:
        model = UserProfile
        fields = [
            "profile_picture",
            "field",
            "target_role",
            "skill_level",
            "tech_preference",
            "learning_goal",
            "interest_tags",
        ]
        widgets = {
            "profile_picture": forms.FileInput(attrs={"accept": "image/*"}),
        }


class UserAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Username"})
        self.fields["password1"].widget.attrs.update({"placeholder": "Password"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm Password"})
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Username"})
        self.fields["password"].widget.attrs.update({"placeholder": "Password"})


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["name", "price", "description", "features"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "features": forms.Textarea(attrs={"rows": 3}),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "field",
            "target_role",
            "skill_level",
            "plan",
            "tech_preference",
            "learning_goal",
            "interest_tags",
            "learning_objectives",
            "resources",
            "task_checklist",
            "detailed_roadmap",
            "premium_hints",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "learning_objectives": forms.Textarea(attrs={"rows": 3}),
            "resources": forms.Textarea(attrs={"rows": 3}),
            "task_checklist": forms.Textarea(attrs={"rows": 3}),
            "detailed_roadmap": forms.Textarea(attrs={"rows": 3}),
            "premium_hints": forms.Textarea(attrs={"rows": 3}),
        }