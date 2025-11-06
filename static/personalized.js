document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Personalized Dashboard JS loaded");

    // --- PROFILE DROPDOWN ---
    const profileIcon = document.getElementById("profileIcon");
    const profileDropdown = document.getElementById("profileDropdown");

    if (profileIcon && profileDropdown) {
        profileIcon.addEventListener("click", () => {
            profileDropdown.classList.toggle("hidden");
        });

        window.addEventListener("click", (e) => {
            if (!profileIcon.contains(e.target) && !profileDropdown.contains(e.target)) {
                profileDropdown.classList.add("hidden");
            }
        });
    }

    // --- COURSE DATA FROM BACKEND ---
    let courseData = {};
    const courseJSON = document.getElementById("courseDataJSON");

    try {
        if (courseJSON && courseJSON.textContent.trim() !== "") {
            courseData = JSON.parse(courseJSON.textContent);
        }
    } catch (err) {
        console.error("⚠️ Error parsing course JSON:", err);
    }

    console.log("📚 Loaded course data:", courseData);

    // --- MODAL ELEMENTS ---
    const detailModal = document.getElementById("detail-modal");
    const closeModalBtn = document.getElementById("closeModal");
    const modalCategoryTitle = document.getElementById("modal-category");
    const modalCourseList = document.getElementById("modal-course-list");
    const categoryInput = document.getElementById("category_code");

    // === MODAL OPEN FUNCTION ===
    function openModal(categoryCode) {
        if (!detailModal) return;

        modalCategoryTitle.textContent = categoryCode.toUpperCase();
        categoryInput.value = categoryCode;

        renderCourses(categoryCode);
        detailModal.classList.remove("hidden");
        document.body.style.overflow = "hidden"; // prevent scroll behind modal
    }

    // === MODAL CLOSE FUNCTION ===
    function closeModal() {
        if (detailModal) {
            detailModal.classList.add("hidden");
            document.body.style.overflow = "auto";
        }
    }

    if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);

    if (detailModal) {
        detailModal.addEventListener("click", (e) => {
            if (e.target === detailModal) closeModal();
        });
    }

    // === RENDER COURSE HISTORY SECTION ===
    function renderCourses(categoryCode) {
    modalCourseList.innerHTML = "";
    const list = courseData[categoryCode] || [];

    if (list.length === 0) {
        modalCourseList.innerHTML = `<p class="no-course">No courses added yet.</p>`;
        return;
    }

    list.forEach((course) => {
        const div = document.createElement("div");
        div.className = "course-item";
        div.innerHTML = `
            <div class="course-info">
                <strong>${course.name}</strong> — ${course.credits} credits
                ${course.grade ? `<span class="grade">Grade: ${course.grade}</span>` : ""}
            </div>
            <button class="delete-btn" data-name="${course.name}" data-cat="${categoryCode}">
                <i class="bi bi-trash"></i> Delete
            </button>
        `;
        modalCourseList.appendChild(div);
    });

    // --- DELETE COURSE HANDLER ---
    const deleteButtons = modalCourseList.querySelectorAll(".delete-btn");
    deleteButtons.forEach((btn) => {
        btn.addEventListener("click", async (e) => {
            const courseName = btn.dataset.name;
            const category = btn.dataset.cat;

            if (confirm(`Are you sure you want to delete "${courseName}"?`)) {
                // Send DELETE request to Flask
                try {
                    const res = await fetch("/delete_course", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ category, course_name: courseName }),
                    });

                    const result = await res.json();
                    if (result.success) {
                        alert("✅ Course deleted successfully!");
                        location.reload(); // refresh to update data
                    } else {
                        alert("⚠️ Failed to delete course.");
                    }
                } catch (err) {
                    console.error("Error deleting course:", err);
                    alert("⚠️ Something went wrong!");
                }
            }
        });
    });
}


    // === ADD COURSE FORM HANDLER ===
    const addCourseForm = document.getElementById("addCourseForm");
    if (addCourseForm) {
        addCourseForm.addEventListener("submit", (e) => {
            const formData = new FormData(addCourseForm);
            const cat = formData.get("category_code");
            const name = formData.get("course_name");
            const credits = formData.get("course_credits");
            const grade = formData.get("course_grade");

            if (!name || !credits) {
                alert("⚠️ Please fill in all required fields.");
                e.preventDefault();
                return;
            }

            console.log(`📘 Adding new course to ${cat}:`, name, credits, grade);
            // Normal form submit (Flask handles DB)
        });
    }

    // === ATTACH EVENTS TO EACH CARD BUTTON ===
    const detailButtons = document.querySelectorAll(".view-details-btn");
    detailButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const cat = btn.dataset.category;
            openModal(cat);
        });
    });

    // === OPTIONAL: ESC KEY TO CLOSE MODAL ===
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closeModal();
    });
});
