import streamlit as st
from datetime import datetime
from typing import List, Optional

# ==========================================
# 1. كائن الوظيفة (Job Model)
# ==========================================
class Job:
    """كائن يمثل الوظيفة داخل التطبيق بأحدث أساليب OOP"""

    def __init__(self, title: str, base_rate: float, required_skills: Optional[List[str]] = None):
        self.title = title
        self.base_rate = base_rate
        self.required_skills = list(required_skills) if required_skills else []
        self.is_active = True
        self.created_at = datetime.now()

    def add_skill(self, skill: str) -> None:
        """إضافة مهارة جديدة للوظيفة"""
        if skill and skill not in self.required_skills:
            self.required_skills.append(skill)

    def deactivate(self) -> None:
        """إلغاء تفعيل الوظيفة"""
        self.is_active = False

    def activate(self) -> None:
        """إعادة تفعيل الوظيفة"""
        self.is_active = True

    # مصانع جاهزة (Factory Methods)
    @classmethod
    def courier_delivery(cls) -> "Job":
        return cls(title="مندوب توصيل", base_rate=30.0, required_skills=["قيادة مركبة", "معرفة الطرق"])

    @classmethod
    def accountant(cls) -> "Job":
        return cls(title="محاسب ماليات", base_rate=60.0, required_skills=["مراجعة الحسابات", "إدخال بيانات"])

    @classmethod
    def admin_support(cls) -> "Job":
        return cls(title="دعم فني إداري", base_rate=45.0, required_skills=["حل المشكلات", "خدمة العملاء"])

    @staticmethod
    def calculate_overtime(hours: float, rate: float) -> float:
        """حساب أجر الساعات الإضافية (1.5x)"""
        return hours * rate * 1.5


# ==========================================
# 2. واجهة التطبيق (Streamlit App)
# ==========================================
st.set_page_config(page_title="نظام إدارة الوظائف", page_icon="💼", layout="wide")

# تهيئة القائمة بالذاكرة المؤقتة لضمان استمرار البيانات أثناء التفاعل
if "jobs_list" not in st.session_state:
    st.session_state.jobs_list = [
        Job.courier_delivery(),
        Job.accountant(),
        Job.admin_support()
    ]

st.title("💼 لوحة إدارة الوظائف والمهام")
st.write("إدارة كاملة لوظائف التطبيق، الأجور، والمهارات المطلوبة.")

# الشريط الجانبي: إدخال وظيفة جديدة أو استدعاء جاهز
with st.sidebar:
    st.header("➕ إضافة وظيفة جديدة")

    # إضافة وظيفة مخصصة
    with st.form("add_job_form", clear_on_submit=True):
        title_input = st.text_input("مسمى الوظيفة")
        rate_input = st.number_input("الأجر الأساسي (بالساعة)", min_value=10.0, value=50.0, step=5.0)
        skills_input = st.text_input("المهارات (افصل بينها بفصلة ,)")
        
        submitted = st.form_submit_button("إضافة الوظيفة")
        if submitted and title_input:
            skills = [s.strip() for s in skills_input.split(",") if s.strip()]
            new_job = Job(title=title_input, base_rate=rate_input, required_skills=skills)
            st.session_state.jobs_list.append(new_job)
            st.success(f"تمت إضافة {title_input} بنجاح!")

    st.divider()
    st.subheader("⚡ إضافة سريعة (مصانع كائنات)")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("+ مندوب"):
            st.session_state.jobs_list.append(Job.courier_delivery())
            st.rerun()
    with col_f2:
        if st.button("+ محاسب"):
            st.session_state.jobs_list.append(Job.accountant())
            st.rerun()

# ==========================================
# 3. عرض الوظائف والتفاعل معها
# ==========================================
st.subheader(f"قائمة الوظائف المتاحة ({len(st.session_state.jobs_list)})")

if not st.session_state.jobs_list:
    st.info("لا يوجد وظائف مسجلة حالياً.")
else:
    for idx, job in enumerate(st.session_state.jobs_list):
        # تمييز الوظيفة النشطة عن الملتغاة
        status_color = "green" if job.is_active else "red"
        status_text = "نشطة" if job.is_active else "معطلة"

        with st.expander(f"🔹 {job.title} | الأجر: {job.base_rate} ج.م | ({status_text})"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**المهارات المطلوبة:** {', '.join(job.required_skills) if job.required_skills else 'لا يوجد'}")
                st.write(f"**تاريخ الإنشاء:** {job.created_at.strftime('%Y-%m-%d %H:%M')}")

                # إضافة مهارة جديدة للكائن مباشرة
                new_skill = st.text_input(f"إضافة مهارة لـ {job.title}", key=f"skill_in_{idx}")
                if st.button("إضافة المهارة", key=f"btn_skill_{idx}"):
                    if new_skill:
                        job.add_skill(new_skill)
                        st.success("تم تحديث المهارات!")
                        st.rerun()

            with col2:
                # حاسبة الساعات الإضافية للوظيفة
                st.write("**حاسبة الأجر الإضافي:**")
                ot_hours = st.number_input("ساعات الإضافي", min_value=0.0, value=2.0, step=0.5, key=f"ot_{idx}")
                ot_pay = Job.calculate_overtime(ot_hours, job.base_rate)
                st.info(f"المبلغ الإضافي: **{ot_pay:.2f} ج.م**")

                # تغيير حالة الوظيفة (تفعيل / إيقاف)
                if job.is_active:
                    if st.button("إيقاف الوظيفة", key=f"deact_{idx}"):
                        job.deactivate()
                        st.rerun()
                else:
                    if st.button("تفعيل الوظيفة", key=f"act_{idx}"):
                        job.activate()
                        st.rerun()
