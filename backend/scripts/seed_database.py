import sys
import os

# Add backend directory and root directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal, engine
from backend.app.core.security import get_password_hash
from backend.app.db.models import (
    Base,
    Role,
    RoleEnum,
    User,
    Department,
    Course,
    Semester,
    AcademicYear,
    Subject,
    Unit,
    Topic,
    LearningOutcome,
    Question,
    QuestionTypeEnum,
    DifficultyLevelEnum,
    BloomLevelEnum,
    QuestionStatusEnum,
    QuestionBank,
    QuestionBankItem,
    Blueprint,
    BlueprintStatusEnum,
    BlueprintRule,
    QuestionPaper,
    QuestionPaperStatusEnum,
    QuestionPaperVersion,
    PaperGenerationMethodEnum,
    QuestionPaperItem,
    AnswerKey,
    AnswerKeyStatusEnum,
    AnswerKeyItem,
)

def seed_database():
    print("[SEED] Starting AI ExamGen Database Seeding Process...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # 1. Seed Roles
        roles_dict = {}
        for role_enum in RoleEnum:
            role = db.query(Role).filter(Role.name == role_enum).first()
            if not role:
                role = Role(
                    name=role_enum,
                    description=f"System role for {role_enum.value.capitalize()}"
                )
                db.add(role)
                db.commit()
                db.refresh(role)
            roles_dict[role_enum.value] = role
        print("[OK] Roles initialized (ADMIN, FACULTY, STUDENT).")

        # 2. Seed Department
        dept = db.query(Department).filter(Department.code == "CSE").first()
        if not dept:
            dept = Department(
                name="Computer Science and Engineering",
                code="CSE",
                description="Department of Computer Science and Engineering",
                is_active=True
            )
            db.add(dept)
            db.commit()
            db.refresh(dept)
        print("[OK] Department initialized (CSE).")

        # 3. Seed Users
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                role_id=roles_dict["ADMIN"].id,
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                first_name="System",
                last_name="Administrator",
                employee_id="ADM-001",
                department_id=dept.id,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        faculty1 = db.query(User).filter(User.email == "faculty@example.com").first()
        if not faculty1:
            faculty1 = User(
                role_id=roles_dict["FACULTY"].id,
                email="faculty@example.com",
                password_hash=get_password_hash("faculty123"),
                first_name="Prof. Alan",
                last_name="Turing",
                employee_id="FAC-001",
                department_id=dept.id,
                is_active=True
            )
            db.add(faculty1)
            db.commit()
            db.refresh(faculty1)

        students = []
        for i in range(1, 6):
            email = f"student{i}@example.com"
            s = db.query(User).filter(User.email == email).first()
            if not s:
                s = User(
                    role_id=roles_dict["STUDENT"].id,
                    email=email,
                    password_hash=get_password_hash("student123"),
                    first_name=f"Student",
                    last_name=f"User {i}",
                    registration_number=f"REG202600{i}",
                    department_id=dept.id,
                    is_active=True
                )
                db.add(s)
                db.commit()
                db.refresh(s)
            students.append(s)
        print("[OK] Users seeded (1 Admin, 1 Faculty, 5 Students).")

        # 4. Seed Course, Academic Year, Semester
        course = db.query(Course).filter(Course.code == "BE-CSE").first()
        if not course:
            course = Course(
                department_id=dept.id,
                name="B.E. Computer Science and Engineering",
                code="BE-CSE",
                description="Four-year undergraduate degree program in Computer Science.",
                duration_years=4,
                is_active=True
            )
            db.add(course)
            db.commit()
            db.refresh(course)

        acad_year = db.query(AcademicYear).filter(AcademicYear.name == "2026-2027").first()
        if not acad_year:
            acad_year = AcademicYear(
                name="2026-2027",
                start_date="2026-06-01",
                end_date="2027-05-31",
                is_current=True
            )
            db.add(acad_year)
            db.commit()
            db.refresh(acad_year)

        semester = db.query(Semester).filter(Semester.number == 3).first()
        if not semester:
            semester = Semester(
                number=3,
                name="Semester 3"
            )
            db.add(semester)
            db.commit()
            db.refresh(semester)
        print("[OK] Course, Academic Year & Semester initialized.")

        # 5. Seed Subject
        subject = db.query(Subject).filter(Subject.code == "CS301").first()
        if not subject:
            subject = Subject(
                course_id=course.id,
                department_id=dept.id,
                semester_id=semester.id,
                academic_year_id=acad_year.id,
                code="CS301",
                name="Data Structures and Algorithms",
                description="Fundamental data structures including linear and non-linear representations, algorithm analysis, sorting, and searching.",
                credits=4,
                total_units=5,
                is_active=True,
                created_by=faculty1.id
            )
            db.add(subject)
            db.commit()
            db.refresh(subject)
        print("[OK] Subject seeded: Data Structures and Algorithms (CS301).")

        # 6. Seed 5 Units & Topics
        units_data = [
            ("Arrays, Strings and Recursion", 1, [
                ("1D & 2D Arrays", ["array", "indexing", "memory layout"]),
                ("String Manipulation", ["strings", "pattern matching"]),
                ("Recursion & Backtracking", ["recursion", "base case", "call stack"])
            ]),
            ("Singly and Doubly Linked Lists", 2, [
                ("Singly Linked List", ["head", "next pointer", "traversal"]),
                ("Doubly Linked List", ["prev pointer", "doubly linked"]),
                ("Circular Linked List", ["circular", "tail node"])
            ]),
            ("Stacks, Queues and Applications", 3, [
                ("Stack Operations", ["LIFO", "push", "pop", "top"]),
                ("Queue Operations", ["FIFO", "enqueue", "dequeue", "front"]),
                ("Infix to Postfix Conversion", ["expression parsing", "operator precedence"])
            ]),
            ("Trees and Binary Search Trees", 4, [
                ("Binary Tree Traversals", ["inorder", "preorder", "postorder"]),
                ("Binary Search Tree (BST)", ["search", "insert", "delete", "O(log n)"]),
                ("AVL Trees & Balancing", ["rotation", "balance factor"])
            ]),
            ("Graphs, Sorting and Searching Algorithms", 5, [
                ("Graph Traversals (BFS & DFS)", ["queue", "stack", "visited array"]),
                ("Sorting Algorithms", ["quicksort", "mergesort", "heapsort"]),
                ("Searching Algorithms", ["binary search", "hash tables", "collisions"])
            ])
        ]

        seeded_units = []
        seeded_topics = []
        for u_title, u_num, topics_list in units_data:
            unit = db.query(Unit).filter(Unit.subject_id == subject.id, Unit.unit_number == u_num).first()
            if not unit:
                unit = Unit(
                    subject_id=subject.id,
                    unit_number=u_num,
                    title=u_title,
                    description=f"Unit {u_num}: {u_title}",
                    weightage=20.0
                )
                db.add(unit)
                db.commit()
                db.refresh(unit)
            seeded_units.append(unit)

            for t_name, kw_list in topics_list:
                top = db.query(Topic).filter(Topic.unit_id == unit.id, Topic.name == t_name).first()
                if not top:
                    top = Topic(
                        unit_id=unit.id,
                        name=t_name,
                        description=f"Topic covering {t_name}",
                        keywords=", ".join(kw_list),
                        importance="HIGH"
                    )
                    db.add(top)
                    db.commit()
                    db.refresh(top)
                seeded_topics.append(top)
        print("[OK] 5 Units & 15 Topics seeded.")

        # 7. Seed Learning Outcomes
        co_data = [
            ("CO1", "Analyze asymptotic time and space complexity of iterative and recursive algorithms.", BloomLevelEnum.ANALYZE),
            ("CO2", "Implement linear data structures including linked lists, stacks, and queues.", BloomLevelEnum.APPLY),
            ("CO3", "Construct and traverse non-linear tree structures and binary search trees.", BloomLevelEnum.CREATE),
            ("CO4", "Apply graph algorithms like BFS, DFS, and shortest path calculations.", BloomLevelEnum.APPLY),
            ("CO5", "Evaluate sorting and searching techniques for optimal computational performance.", BloomLevelEnum.EVALUATE)
        ]

        seeded_cos = []
        for code, desc, bloom in co_data:
            co = db.query(LearningOutcome).filter(LearningOutcome.subject_id == subject.id, LearningOutcome.code == code).first()
            if not co:
                co = LearningOutcome(
                    subject_id=subject.id,
                    code=code,
                    description=desc,
                    bloom_level=bloom
                )
                db.add(co)
                db.commit()
                db.refresh(co)
            seeded_cos.append(co)
        print("[OK] 5 Learning Outcomes (CO1 to CO5) seeded.")

        # 8. Seed 20+ Questions
        raw_questions = [
            # Unit 1
            ("What is the worst-case time complexity of accessing an element in an array by index?", QuestionTypeEnum.MCQ, 2.0, DifficultyLevelEnum.EASY, BloomLevelEnum.REMEMBER, 0, 0, "O(1)", ["O(1)", "constant time"], ["direct indexing", "contiguous memory"]),
            ("Define recursion and state the purpose of a base case in recursive functions.", QuestionTypeEnum.SHORT_ANSWER, 2.0, DifficultyLevelEnum.EASY, BloomLevelEnum.UNDERSTAND, 0, 2, "Recursion is a technique where a function calls itself. The base case stops infinite recursion.", ["recursion", "base case", "call stack"], ["self invocation", "termination condition"]),
            ("Explain the concept of dynamic array reallocation and its amortized time complexity.", QuestionTypeEnum.DESCRIPTIVE, 5.0, DifficultyLevelEnum.MEDIUM, BloomLevelEnum.ANALYZE, 0, 0, "Dynamic arrays double capacity when full. Amortized cost per insertion is O(1).", ["dynamic array", "amortized", "doubling"], ["capacity expansion", "aggregate analysis"]),
            
            # Unit 2
            ("Differentiate between a Singly Linked List and a Doubly Linked List in terms of memory and traversal.", QuestionTypeEnum.SHORT_ANSWER, 2.0, DifficultyLevelEnum.EASY, BloomLevelEnum.UNDERSTAND, 1, 0, "Singly linked lists store next pointers. Doubly linked lists store both prev and next pointers allowing bidirectional traversal.", ["singly linked list", "doubly linked list", "prev pointer", "bidirectional"], ["pointer overhead", "node structure"]),
            ("Write an algorithm to insert a new node at the beginning of a Singly Linked List.", QuestionTypeEnum.PROBLEM_SOLVING, 5.0, DifficultyLevelEnum.MEDIUM, BloomLevelEnum.APPLY, 1, 0, "Set newNode.next = head; head = newNode;", ["newNode", "head", "next pointer", "O(1) insertion"], ["head reference update", "pointer assignment"]),
            ("Explain how to detect a loop in a linked list using Floyd's Cycle Detection algorithm.", QuestionTypeEnum.DESCRIPTIVE, 13.0, DifficultyLevelEnum.HARD, BloomLevelEnum.ANALYZE, 1, 0, "Use slow pointer (1 step) and fast pointer (2 steps). If slow == fast, a cycle exists.", ["slow pointer", "fast pointer", "Floyd's algorithm", "cycle detection"], ["hare and tortoise", "pointer intersection"]),

            # Unit 3
            ("A stack follows which data structural discipline?", QuestionTypeEnum.MCQ, 2.0, DifficultyLevelEnum.EASY, BloomLevelEnum.REMEMBER, 2, 0, "Last In First Out (LIFO)", ["LIFO", "Last In First Out"], ["push pop operations"]),
            ("Convert the infix expression A + B * C to postfix notation.", QuestionTypeEnum.PROBLEM_SOLVING, 2.0, DifficultyLevelEnum.MEDIUM, BloomLevelEnum.APPLY, 2, 2, "ABC*+", ["ABC*+", "postfix", "operator precedence"], ["stack evaluation", "operator stack"]),
            ("Explain the implementation of a Queue using two Stacks and analyze its time complexity.", QuestionTypeEnum.PROBLEM_SOLVING, 13.0, DifficultyLevelEnum.HARD, BloomLevelEnum.APPLY, 2, 1, "Use inStack for enqueue and outStack for dequeue. When outStack is empty, pop all elements from inStack to outStack.", ["inStack", "outStack", "enqueue", "dequeue", "amortized O(1)"], ["stack transfer", "LIFO to FIFO"]),

            # Unit 4
            ("Which traversal of a Binary Search Tree produces elements in sorted order?", QuestionTypeEnum.MCQ, 2.0, DifficultyLevelEnum.EASY, BloomLevelEnum.REMEMBER, 3, 0, "Inorder traversal", ["inorder", "sorted order"], ["tree traversal"]),
            ("Explain Binary Search Tree (BST) insertion and search operations with time complexity analysis.", QuestionTypeEnum.DESCRIPTIVE, 13.0, DifficultyLevelEnum.MEDIUM, BloomLevelEnum.ANALYZE, 3, 1, "BST search compares value with current node: go left if smaller, right if larger. Time complexity O(h).", ["binary search tree", "left child", "right child", "O(log n)", "O(n) worst case"], ["dividing search space", "height balance"]),
            ("Demonstrate AVL tree single and double rotations with a concrete insertion example.", QuestionTypeEnum.DESCRIPTIVE, 15.0, DifficultyLevelEnum.HARD, BloomLevelEnum.CREATE, 3, 2, "AVL tree maintains balance factor between -1 and +1 using LL, RR, LR, and RL rotations.", ["AVL tree", "balance factor", "rotations", "LL RR LR RL"], ["height rebalancing", "tree node rotation"]),

            # Unit 5
            ("What is the average and worst-case time complexity of QuickSort?", QuestionTypeEnum.SHORT_ANSWER, 2.0, DifficultyLevelEnum.EASY, BloomLevelEnum.REMEMBER, 4, 1, "Average case: O(n log n). Worst case: O(n^2).", ["O(n log n)", "O(n^2)", "QuickSort"], ["partitioning", "pivot selection"]),
            ("Write a C/C++ or Python program to implement Binary Search on a sorted array.", QuestionTypeEnum.PROGRAMMING, 13.0, DifficultyLevelEnum.MEDIUM, BloomLevelEnum.APPLY, 4, 1, "Binary search repeatedly divides search interval in half comparing target with mid element.", ["binary search", "sorted array", "low high mid", "O(log n)"], ["divide and conquer", "middle index comparison"]),
            ("Compare Breadth First Search (BFS) and Depth First Search (DFS) in terms of data structures used and application domains.", QuestionTypeEnum.DESCRIPTIVE, 13.0, DifficultyLevelEnum.MEDIUM, BloomLevelEnum.ANALYZE, 4, 0, "BFS uses Queue (level order), DFS uses Stack / Recursion (path traversal).", ["BFS", "DFS", "Queue", "Stack", "level order", "backtracking"], ["graph exploration", "shortest path"]),
        ]

        seeded_questions = []
        for q_tuple in raw_questions:
            q_text, q_type, q_marks, q_diff, q_bloom, u_idx, t_offset, ans, kws, concs = q_tuple
            target_unit = seeded_units[u_idx]
            target_topic = seeded_topics[min(u_idx * 3 + t_offset, len(seeded_topics) - 1)]
            target_co = seeded_cos[u_idx]

            q = db.query(Question).filter(Question.subject_id == subject.id, Question.question_text == q_text).first()
            if not q:
                q = Question(
                    subject_id=subject.id,
                    unit_id=target_unit.id,
                    topic_id=target_topic.id,
                    learning_outcome_id=target_co.id,
                    question_text=q_text,
                    question_type=q_type,
                    marks=q_marks,
                    difficulty=q_diff,
                    bloom_level=q_bloom,
                    expected_answer=ans,
                    keywords=kws,
                    concepts=concs,
                    source="MANUAL",
                    status=QuestionStatusEnum.ACTIVE,
                    created_by=faculty1.id
                )
                db.add(q)
                db.commit()
                db.refresh(q)
            seeded_questions.append(q)
        print(f"[OK] {len(seeded_questions)} Questions seeded across all 5 units.")

        # 9. Seed Question Bank
        qbank = db.query(QuestionBank).filter(QuestionBank.subject_id == subject.id).first()
        if not qbank:
            qbank = QuestionBank(
                subject_id=subject.id,
                name="CS301 DSA Master Question Bank",
                description="Comprehensive question bank for Data Structures & Algorithms",
                created_by=faculty1.id
            )
            db.add(qbank)
            db.commit()
            db.refresh(qbank)

            for q in seeded_questions:
                qb_item = QuestionBankItem(
                    question_bank_id=qbank.id,
                    question_id=q.id,
                    added_by=faculty1.id
                )
                db.add(qb_item)
            db.commit()
        print("[OK] Question Bank seeded with all questions.")

        # 10. Seed Blueprint & Rules
        blueprint = db.query(Blueprint).filter(Blueprint.subject_id == subject.id).first()
        if not blueprint:
            blueprint = Blueprint(
                subject_id=subject.id,
                name="End-Semester 100-Mark Examination Blueprint",
                description="Standard university paper pattern: Part A (10x2=20), Part B (5x13=65), Part C (1x15=15)",
                total_marks=100.0,
                duration_minutes=180,
                status=BlueprintStatusEnum.ACTIVE,
                created_by=faculty1.id
            )
            db.add(blueprint)
            db.commit()
            db.refresh(blueprint)

            rules = [
                BlueprintRule(blueprint_id=blueprint.id, section="Part A", question_count=10, marks_per_question=2.0, total_marks=20.0, difficulty=DifficultyLevelEnum.EASY, order_index=1),
                BlueprintRule(blueprint_id=blueprint.id, section="Part B", question_count=5, marks_per_question=13.0, total_marks=65.0, difficulty=DifficultyLevelEnum.MEDIUM, order_index=2),
                BlueprintRule(blueprint_id=blueprint.id, section="Part C", question_count=1, marks_per_question=15.0, total_marks=15.0, difficulty=DifficultyLevelEnum.HARD, order_index=3)
            ]
            db.add_all(rules)
            db.commit()
        print("[OK] Blueprint & Rules seeded.")

        # 11. Seed Question Paper, Paper Version & Paper Items
        qpaper = db.query(QuestionPaper).filter(QuestionPaper.paper_code == "CS301-2026-FINAL").first()
        if not qpaper:
            qpaper = QuestionPaper(
                subject_id=subject.id,
                blueprint_id=blueprint.id,
                title="End Semester Examination - Data Structures and Algorithms",
                paper_code="CS301-2026-FINAL",
                total_marks=100.0,
                duration_minutes=180,
                status=QuestionPaperStatusEnum.APPROVED,
                created_by=faculty1.id
            )
            db.add(qpaper)
            db.commit()
            db.refresh(qpaper)

            paper_ver = QuestionPaperVersion(
                question_paper_id=qpaper.id,
                version_number=1,
                generation_method=PaperGenerationMethodEnum.HYBRID,
                generated_by=faculty1.id,
                generation_metadata={"ai_model": "gemini-1.5-pro", "blueprint_matched": True}
            )
            db.add(paper_ver)
            db.commit()
            db.refresh(paper_ver)

            # Insert paper items with text snapshots
            for idx, q in enumerate(seeded_questions[:10], start=1):
                item = QuestionPaperItem(
                    question_paper_version_id=paper_ver.id,
                    question_id=q.id,
                    section="Part A" if idx <= 6 else ("Part B" if idx <= 9 else "Part C"),
                    question_number=f"Q{idx}",
                    marks=q.marks,
                    question_text_snapshot=q.question_text,
                    order_index=idx
                )
                db.add(item)
            db.commit()
            print("[OK] Question Paper & Paper Version 1 seeded with historical snapshots.")

            # 12. Seed Answer Key & Items
            answer_key = AnswerKey(
                question_paper_version_id=paper_ver.id,
                version_number=1,
                status=AnswerKeyStatusEnum.APPROVED,
                generated_by=faculty1.id,
                approved_by=faculty1.id
            )
            db.add(answer_key)
            db.commit()
            db.refresh(answer_key)

            paper_items = db.query(QuestionPaperItem).filter(QuestionPaperItem.question_paper_version_id == paper_ver.id).all()
            for p_item in paper_items:
                orig_q = db.query(Question).get(p_item.question_id)
                ak_item = AnswerKeyItem(
                    answer_key_id=answer_key.id,
                    question_paper_item_id=p_item.id,
                    model_answer=orig_q.expected_answer if orig_q else "Expected model answer text.",
                    keywords=orig_q.keywords if orig_q else ["keyword1"],
                    concepts=orig_q.concepts if orig_q else ["concept1"],
                    maximum_marks=p_item.marks
                )
                db.add(ak_item)
            db.commit()
            print("[OK] Answer Key & Answer Key Items seeded.")

        print("[SUCCESS] AI ExamGen Database Seeding Complete!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
