from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from app.models import Admission
from app.utils import get_steps
import logging

logger = logging.getLogger(__name__)


TWELFTH_FIELDS = [
    "twelfth_total", "twelfth_percentage",
    "maths_marks", "physics_marks",
    "chemistry_marks", "twelfth_major"
]

DIPLOMA_FIELDS = [
    "diploma_total", "diploma_percentage", "diploma_major"
]


def clear_fields(instance, fields):
    """Utility to clear model fields safely"""
    for field in fields:
        setattr(instance, field, None)


def marks_obtained(request, pk):
    admission = Admission.objects.filter(pk=pk).first()
    if not admission:
        messages.error(request, "Admission record not found.")
        return redirect("personal_details")

    if request.method == "POST":
        data = request.POST

        tenth_total = data.get("tenth_total", "").strip()
        tenth_percentage = data.get("tenth_percentage", "").strip()
        qualification = data.get("qualification", "").strip()

        if not all([tenth_total, tenth_percentage, qualification]):
            messages.error(request, "Please fill all required fields.")
            return render(request, "details_form/marks_obtained.html", {"admission": admission})

        # ---- 10th Percentage Validation ----
        try:
            tenth_pct = float(tenth_percentage)
            if not 0 <= tenth_pct <= 100:
                raise ValueError
        except ValueError:
            messages.error(request, "10th percentage must be between 0 and 100.")
            return render(request, "details_form/marks_obtained.html", {"admission": admission})

        cutoff_marks = None

        # ================= QUALIFICATION LOGIC =================
        if qualification == "12th":
            try:
                maths = float(data.get("maths_marks", ""))
                physics = float(data.get("physics_marks", ""))
                chemistry = float(data.get("chemistry_marks", ""))
            except ValueError:
                messages.error(request, "Invalid numeric marks for 12th.")
                return render(request, "details_form/marks_obtained.html", {"admission": admission})

            required = ["twelfth_total", "twelfth_major"]
            if not all(data.get(f) for f in required):
                messages.error(request, "Please fill all 12th qualification fields.")
                return render(request, "details_form/marks_obtained.html", {"admission": admission})

            cutoff_marks = maths + (physics / 2) + (chemistry / 2)

            # Clear Diploma Fields
            clear_fields(admission, DIPLOMA_FIELDS)

            # Assign 12th fields
            for field in TWELFTH_FIELDS:
                setattr(admission, field, data.get(field) or None)

        elif qualification == "Diploma":
            try:
                diploma_pct = float(data.get("diploma_percentage", ""))
                if not 0 <= diploma_pct <= 100:
                    raise ValueError
            except ValueError:
                messages.error(request, "Diploma percentage must be between 0 and 100.")
                return render(request, "details_form/marks_obtained.html", {"admission": admission})

            if not all(data.get(f) for f in DIPLOMA_FIELDS):
                messages.error(request, "Please fill all Diploma qualification fields.")
                return render(request, "details_form/marks_obtained.html", {"admission": admission})

            cutoff_marks = 0

            # Clear 12th Fields
            clear_fields(admission, TWELFTH_FIELDS)

            # Assign Diploma fields
            for field in DIPLOMA_FIELDS:
                setattr(admission, field, data.get(field) or None)
            admission.level = "le"

        else:
            messages.error(request, "Invalid qualification selected.")
            return render(request, "details_form/marks_obtained.html", {"admission": admission})

        # ================= SAVE =================
        try:
            admission.tenth_total = tenth_total
            admission.tenth_percentage = tenth_pct
            admission.qualification = qualification
            admission.cutoff_marks = cutoff_marks

            admission.full_clean()
            admission.save()

            logger.info("Marks saved for admission %s", admission.pk)
            messages.success(request, "Marks details saved successfully.")
            return redirect("academic_info", pk=pk)

        except ValidationError as e:
            logger.warning("Validation error: %s", e)
            messages.error(request, e.message_dict)
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            messages.error(request, "Error while saving marks.")

    return render(
        request,
        "details_form/marks_obtained.html",
        {
            "admission": admission,
            "steps": get_steps(),
            "current_step": 3,
        },
    )
