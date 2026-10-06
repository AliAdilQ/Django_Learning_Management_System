"""Idempotent development data. Never changes passwords of existing users."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from assignments.models import Assignment, Submission
from courses.models import (
    Announcement,
    Category,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    Module,
    Review,
)
from quizzes.models import Choice, Question, Quiz, QuizAnswer, QuizAttempt

CATALOG = [
    (
        "Python Programming",
        "code-slash",
        "Start with the foundations of Python, from readable code to useful everyday programs.",
    ),
    (
        "Machine Learning",
        "cpu",
        "Understand how models learn patterns and how to evaluate them thoughtfully.",
    ),
    (
        "Web Development",
        "globe",
        "Build useful, accessible web applications with modern Python frameworks.",
    ),
    (
        "Data Science",
        "bar-chart",
        "Ask better questions of data and turn your findings into clear stories.",
    ),
    (
        "Artificial Intelligence",
        "stars",
        "Explore intelligent systems, responsible design, and the ideas behind AI.",
    ),
    (
        "Natural Language Processing",
        "chat",
        "Discover how computers represent, analyze, and work with human language.",
    ),
]

# Each lesson is real introductory demo content, with a concrete practice task.
COURSES = [
    {
        "title": "Python Programming Fundamentals",
        "category": "Python Programming",
        "art": "python",
        "level": "beginner",
        "hours": 8,
        "short": "Your first line of code is the start of something great. Learn Python by building.",
        "description": "Build a confident foundation in Python with small, practical exercises. Start with values and variables, then use decisions, loops, and functions to turn an idea into a working program.\n\nBy the end, you will be able to read simple Python programs, model everyday data, and break a task into reusable functions. Your final assignment brings those skills together in a command-line habit tracker.\n\nNo prior programming experience is required. Install Python 3.12 or newer and bring a text editor. This is an introductory demonstration curriculum for the LMS portfolio.",
        "modules": [
            (
                "Your first steps in Python",
                [
                    (
                        "Welcome to your Python journey",
                        "Python is a general-purpose programming language that emphasizes readable code. A program is a sequence of instructions; the interpreter executes them from top to bottom.\n\nCreate a file named hello.py and add: print('Hello, curious mind!'). Run it with python hello.py. Change the message and run the file again. You have already completed the edit-run-observe cycle used in much larger projects.\n\nPractice: print your name, a skill you want to learn, and a small goal for today. Keep each message on its own line.",
                    ),
                    (
                        "Variables and everyday data",
                        "A variable gives a name to a value. For example, minutes = 20 binds the integer 20 to the name minutes. Python also has strings, floats, and booleans. Use names that describe the data, such as learner_name or lesson_minutes.\n\nTry learner_name = 'Alex' and print(f'{learner_name} studied for {minutes} minutes'). Reassign minutes and observe the result. input() returns a string, so convert with int() before doing arithmetic.\n\nPractice: ask for a name and a daily learning goal, then print a friendly summary. Handle a non-numeric goal with try and except ValueError.",
                    ),
                    (
                        "Lists, dictionaries, and useful collections",
                        "Lists keep values in an order: topics = ['variables', 'loops', 'functions']. Access the first item with topics[0], add with append(), and iterate with for. Dictionaries associate keys with values, such as progress = {'variables': True, 'loops': False}.\n\nChoose a list when position matters and a dictionary when you want to look something up by name. Avoid modifying a list while iterating over it; build a new list instead.\n\nPractice: store three learning goals in a list and a completion flag for each goal in a dictionary. Print each goal and its current status.",
                    ),
                ],
            ),
            (
                "Turn ideas into programs",
                [
                    (
                        "Make decisions with conditionals",
                        "An if statement selects a branch based on a boolean expression. Use if minutes >= 20: to celebrate a daily goal, then elif and else for other outcomes. Indentation defines which statements belong to each branch.\n\nUse == to compare values and = to assign them. Combine conditions with and, or, and not. Prefer a few clear branches over a deeply nested decision tree.\n\nPractice: write a program that labels learning sessions as short, focused, or deep based on duration. Test boundary values such as 0, 19, 20, and 60.",
                    ),
                    (
                        "Repeat actions with loops",
                        "A for loop processes each item in an iterable. A while loop repeats while a condition remains true. For a fixed collection, use for; for an interactive menu, a while loop can be appropriate.\n\nTry for topic in topics: followed by print(topic). Use range(1, 4) to generate 1, 2, and 3. A while loop must eventually change its condition or use break to avoid running forever.\n\nPractice: sum a list of daily study minutes and print the weekly total. Then display each day's minutes with enumerate(..., start=1).",
                    ),
                    (
                        "Write your first reusable function",
                        "A function names a reusable piece of behavior. Define def completion_rate(done, total): and return a calculated percentage. Return 0 when total is 0 to avoid division by zero.\n\nKeep a function focused, use parameters instead of global state, and return data rather than printing inside every function. This makes your code easier to test and reuse.\n\nPractice: write completion_rate, then test it with (0, 0), (2, 4), and (4, 4). Use the result in your habit tracker to summarize progress.",
                    ),
                ],
            ),
        ],
        "questions": [
            (
                "Which expression creates a Python list?",
                ["[1, 2, 3]", "{1: 2}", "(1, 2, 3)", "'1, 2, 3'"],
                0,
            ),
            (
                "What does a function's return statement do?",
                [
                    "Prints a message",
                    "Sends a value back to the caller",
                    "Repeats a loop",
                    "Imports a module",
                ],
                1,
            ),
            ("Which keyword handles an alternative branch?", ["def", "for", "else", "import"], 2),
        ],
    },
    {
        "title": "Django Web Development",
        "category": "Web Development",
        "art": "django",
        "level": "intermediate",
        "hours": 12,
        "short": "Bring your ideas to the web with models, views, and a little Django magic.",
        "description": "Create a maintainable web application with Django's model-template-view architecture. Learn how a request moves through URL routing, views, templates, and the ORM.\n\nYou will work with database migrations, validated forms, authentication, and access control. The final project is a reading-list app where users can manage only their own books.\n\nComfort with Python functions and classes is recommended. The examples use SQLite and Django 5.2. Sample material is introductory, rather than a complete professional qualification.",
        "modules": [
            (
                "Build the foundation",
                [
                    (
                        "How a Django request works",
                        "A browser sends an HTTP request. Django matches its path against urlpatterns and calls the selected view. The view reads data and returns an HttpResponse, often by rendering a template.\n\nCreate a project and a books app. Add a named URL for a book listing and a view that renders books/list.html. Use the URL name in template links instead of hardcoding paths.\n\nPractice: trace a GET request from the browser through the route, view, and template. Change the greeting in the view context and observe the result.",
                    ),
                    (
                        "Model your data with the ORM",
                        "A Django model describes stored data. A Book might have a title, author, owner, and created_at timestamp. ForeignKey represents a relationship, while QuerySets let you filter data using Python.\n\nUse Book.objects.filter(owner=request.user) for a user's collection. select_related('owner') can fetch a foreign key in the same query. Do not build raw SQL from user input.\n\nPractice: define the Book model and add a helpful __str__ method. Create two books in the Django shell and query them by author.",
                    ),
                    (
                        "Make database changes with migrations",
                        "Migrations record changes to model structure. makemigrations generates migration files; migrate applies them to the database. Commit migrations with the source code so a fresh checkout can reproduce the schema.\n\nBefore adding a required field to populated data, decide how existing rows should receive a value. Review generated migration files and use showmigrations to inspect applied changes.\n\nPractice: add an optional summary to Book, generate a migration, and apply it. Confirm existing books remain accessible.",
                    ),
                ],
            ),
            (
                "Create a safe user experience",
                [
                    (
                        "Reuse layouts with template inheritance",
                        "A base template owns shared navigation, styles, and footer. Child templates fill blocks, while includes provide reusable fragments. Django escapes variable output by default, protecting users from injected markup.\n\nUse {% extends 'base.html' %} and a content block. Keep user-authored book summaries escaped; do not apply the safe filter to untrusted content.\n\nPractice: build a shared book card and render it on the homepage and reading list. Add a meaningful empty state when no books are available.",
                    ),
                    (
                        "Validate input with ModelForms",
                        "A ModelForm maps selected model fields to validated inputs. Bind request.POST on POST, call is_valid(), and use cleaned_data or save(). Explicitly list fields so clients cannot submit protected attributes.\n\nSet the owner in the view after form.save(commit=False). Include a CSRF token and redirect after a successful POST to avoid accidental repeat submissions.\n\nPractice: create a book form with title, author, and summary. Submit an empty title and check that the error is displayed beside the field.",
                    ),
                    (
                        "Authentication and object permissions",
                        "Authentication answers who a user is. Authorization answers what that user may do. login_required protects a view from anonymous users, but it does not establish ownership of an individual book.\n\nRetrieve editable books with get_object_or_404(Book, pk=pk, owner=request.user). Never trust an owner identifier supplied by the browser. Use POST for destructive actions.\n\nPractice: create two users and verify that one cannot edit the other's book by changing a URL or a submitted identifier.",
                    ),
                ],
            ),
        ],
        "questions": [
            (
                "What command applies migrations?",
                ["runserver", "migrate", "startapp", "collectstatic"],
                1,
            ),
            (
                "What protects a form POST from cross-site forgery?",
                ["A CSRF token", "A CSS class", "An image", "A page title"],
                0,
            ),
            (
                "Where should a book's owner be assigned?",
                [
                    "A public hidden input",
                    "An unvalidated query parameter",
                    "The server using the authenticated user",
                    "The browser's local storage",
                ],
                2,
            ),
        ],
    },
    {
        "title": "Flask Web Development",
        "category": "Web Development",
        "art": "flask",
        "level": "beginner",
        "hours": 7,
        "short": "Small framework, big possibilities. Create a lightweight Python web application.",
        "description": "Explore Flask by building a small notes application. Connect routes, templates, forms, and persistent data while keeping your project understandable.\n\nYou will learn about HTTP methods, escaping, configuration, and application structure. Familiarity with basic Python is helpful. The sample project uses local data and focuses on foundational concepts.",
        "modules": [
            (
                "Routes and responses",
                [
                    (
                        "Start a minimal Flask application",
                        "Flask maps routes to Python functions. Create an application and a route for /. The function can return text or rendered HTML. Keep debug mode limited to development.\n\nPractice: add a /notes/ route that returns a greeting, then inspect its response in your browser.",
                    ),
                    (
                        "Understand GET and POST",
                        "GET retrieves information; POST submits a change. Form fields arrive as request data and must be validated before use. A successful POST usually redirects to a GET page.\n\nPractice: sketch the request sequence for adding a note. Identify what must be checked before saving it.",
                    ),
                    (
                        "Create readable Jinja templates",
                        "Templates separate page structure from view logic. Jinja's inheritance lets multiple pages share a layout. Use automatic escaping and meaningful labels for form inputs.\n\nPractice: create a base layout and a notes page with an empty state.",
                    ),
                ],
            ),
            (
                "A maintainable small application",
                [
                    (
                        "Organize routes with blueprints",
                        "Blueprints group related routes. An application factory creates an app with explicit configuration, making different test and development setups easier.\n\nPractice: move note routes into a blueprint and register it in your factory.",
                    ),
                    (
                        "Persist notes in SQLite",
                        "SQLite stores structured data in a local file. Parameterized queries separate data from query structure; never concatenate user input into SQL.\n\nPractice: design a notes table with title, content, and created time. Describe how a form maps to its columns.",
                    ),
                    (
                        "Test routes and validation",
                        "A test client can exercise routes without starting a public server. Test successful creation and invalid inputs, and use a separate test database.\n\nPractice: list tests for an empty note, a missing page, and a successful redirect after creation.",
                    ),
                ],
            ),
        ],
        "questions": [
            ("Which HTTP method should create a note?", ["GET", "POST", "HEAD", "OPTIONS"], 1),
            (
                "What helps prevent SQL injection?",
                ["String concatenation", "Parameterized queries", "CSS", "Longer route names"],
                1,
            ),
            (
                "What groups related Flask routes?",
                ["A blueprint", "A favicon", "A stylesheet", "A browser tab"],
                0,
            ),
        ],
    },
    {
        "title": "Machine Learning Essentials",
        "category": "Machine Learning",
        "art": "machine-learning",
        "level": "intermediate",
        "hours": 10,
        "short": "Find the signal in the noise. Understand models, patterns, and predictions.",
        "description": "Learn the reasoning behind a reliable machine learning workflow. Frame a problem, split data carefully, establish a baseline, and evaluate a model with useful metrics.\n\nThe final assignment compares a baseline and a simple classifier using a reproducible experiment. Basic Python and familiarity with tables are recommended. This curriculum uses small educational datasets.",
        "modules": [
            (
                "From data to a learning problem",
                [
                    (
                        "Supervised and unsupervised learning",
                        "Supervised learning uses examples with target labels. Classification predicts categories and regression predicts numbers. Unsupervised methods discover structure without supplied target labels.\n\nPractice: classify house-price prediction, spam detection, and customer clustering by learning type.",
                    ),
                    (
                        "Features, labels, and leakage",
                        "Features are inputs available at prediction time. A label is the target. Leakage occurs when training uses information that would not be available in a real prediction, making evaluation overly optimistic.\n\nPractice: inspect an imaginary loan dataset and remove fields recorded only after repayment.",
                    ),
                    (
                        "Split data before fitting",
                        "Hold out test data before fitting transformations. Fit scaling or imputation using training data only, then transform validation and test sets consistently. For time-dependent data, preserve temporal order.\n\nPractice: describe a split strategy for predicting tomorrow's demand and explain why a random split may mislead.",
                    ),
                ],
            ),
            (
                "Evaluate with care",
                [
                    (
                        "Build a useful baseline",
                        "A baseline gives context to model performance. Predicting the most common class or the training mean is often a useful starting point. A complex model must improve on it for the right reason.\n\nPractice: calculate baseline accuracy for a dataset with 90 positive and 10 negative examples.",
                    ),
                    (
                        "Choose metrics that match the task",
                        "Accuracy can hide poor minority-class performance. Precision measures how many positive predictions are correct; recall measures how many actual positives were found. A confusion matrix shows the error types.\n\nPractice: discuss which error matters more in a spam filter and justify a metric.",
                    ),
                    (
                        "Generalization and overfitting",
                        "An overfit model learns details of training data that do not transfer. Compare training and validation performance, simplify where appropriate, and reserve the test set for final evaluation.\n\nPractice: write a short experiment report with the split, baseline, metric, result, and limitations.",
                    ),
                ],
            ),
        ],
        "questions": [
            (
                "What is a label in supervised learning?",
                ["The target value", "A filename", "A chart color", "A random feature"],
                0,
            ),
            (
                "Which data should fit a scaler?",
                ["The whole dataset", "Only test data", "Only training data", "Future labels"],
                2,
            ),
            (
                "What does a baseline provide?",
                ["Guaranteed accuracy", "A comparison point", "More labels", "Perfect fairness"],
                1,
            ),
        ],
    },
    {
        "title": "Data Science with Python",
        "category": "Data Science",
        "art": "data-science",
        "level": "intermediate",
        "hours": 11,
        "short": "Ask better questions. Turn everyday data into insights that tell a story.",
        "description": "Work through a clear data-analysis process with Python. Inspect a dataset, handle missing values thoughtfully, summarize patterns, and communicate findings with honest charts.\n\nYour final assignment analyzes a small learning-activity dataset and presents three supported findings. Basic Python is recommended. Emphasis is on reproducible reasoning and communication.",
        "modules": [
            (
                "Know your data",
                [
                    (
                        "Start with a question",
                        "Useful analysis begins with a question and a decision it can inform. Identify the unit of observation, relevant variables, and how the data was collected before choosing tools.\n\nPractice: turn 'analyze study data' into a precise question about session duration and completion.",
                    ),
                    (
                        "Inspect a DataFrame",
                        "A DataFrame is a labeled table. Inspect column types, row counts, missing values, and duplicates before computing summaries. Keep a record of cleaning decisions.\n\nPractice: create a checklist for validating a CSV with student, topic, minutes, and completion columns.",
                    ),
                    (
                        "Handle missing data thoughtfully",
                        "Missing data can have different causes. Removing rows or filling values changes the analysis, so explain your assumption and check sensitivity. A missing measurement is not automatically zero.\n\nPractice: compare how a mean changes when missing session lengths are dropped versus treated as zero.",
                    ),
                ],
            ),
            (
                "Find and communicate patterns",
                [
                    (
                        "Summarize with group operations",
                        "Group operations aggregate records by a category. Consider sample size and outliers alongside averages. Medians can provide a useful description for skewed durations.\n\nPractice: sketch a table of study minutes by topic with count, median, and maximum.",
                    ),
                    (
                        "Choose an honest visualization",
                        "Bar charts compare categories, line charts show ordered change, and scatter plots show relationships. Label units, avoid misleading axis choices, and distinguish observations from interpretations.\n\nPractice: choose a chart for weekly study time and write an informative title.",
                    ),
                    (
                        "Tell a reproducible data story",
                        "A good report connects a question, method, evidence, and limitation. Association does not establish causation. Preserve source data and record transformations so another analyst can reproduce the result.\n\nPractice: write three findings about learning activity, each with a caveat and a supporting summary.",
                    ),
                ],
            ),
        ],
        "questions": [
            (
                "What should come before analysis?",
                ["A clear question", "A random chart", "A production server", "A new logo"],
                0,
            ),
            (
                "Which chart suits change over time?",
                ["A line chart", "A pie for every row", "An unlabeled image", "A decorative icon"],
                0,
            ),
            (
                "Does correlation alone prove causation?",
                ["Always", "No", "Only in Python", "Only for large files"],
                1,
            ),
        ],
    },
    {
        "title": "Natural Language Processing",
        "category": "Natural Language Processing",
        "art": "nlp",
        "level": "advanced",
        "hours": 9,
        "short": "Explore the space between words and meaning. Make human language computable.",
        "description": "Explore foundational NLP concepts, from tokens and vector representations to evaluation of a text classifier. Consider how preprocessing changes meaning and how language data introduces ambiguity.\n\nYour assignment designs a sentiment-classification experiment with explicit limitations. Python and basic machine learning knowledge are recommended.",
        "modules": [
            (
                "Represent human language",
                [
                    (
                        "Tokens and normalization",
                        "Tokenization divides text into units. Lowercasing and punctuation removal may help some tasks but can erase useful signals such as names, emphasis, or sentence boundaries.\n\nPractice: tokenize 'I can't believe it!' in two different ways and describe the tradeoffs.",
                    ),
                    (
                        "Build a bag-of-words representation",
                        "Bag-of-words represents a document by token counts without retaining word order. It is simple and useful as a baseline, but cannot fully distinguish sentences that use the same words differently.\n\nPractice: compare counts for 'the cat chased the dog' and 'the dog chased the cat'.",
                    ),
                    (
                        "Understand embeddings",
                        "An embedding represents a token or text as a numeric vector. Similarity reflects patterns learned from data, not guaranteed shared meaning. Contextual representations can vary with surrounding words.\n\nPractice: explain why 'bank' needs context and list two sentences with different meanings.",
                    ),
                ],
            ),
            (
                "Evaluate language systems",
                [
                    (
                        "Frame a text classification task",
                        "Define labels precisely and decide how ambiguous cases are handled. Annotation guidelines and agreement matter as much as model choice. Split related documents together to avoid leakage.\n\nPractice: write guidelines for positive, negative, and mixed course reviews.",
                    ),
                    (
                        "Inspect errors beyond the score",
                        "A single metric can hide systematic errors. Inspect negation, sarcasm, language variation, and minority examples. Record concrete error categories alongside aggregate metrics.\n\nPractice: make a small test set containing 'not bad', sarcasm, and a mixed review.",
                    ),
                    (
                        "Responsible use of language data",
                        "Text can contain personal information and social bias. Use appropriate data permissions, minimize sensitive content, and describe intended use and limitations. Do not infer reliable intent from a short sentence alone.\n\nPractice: document one privacy risk and one limitation of your proposed classifier.",
                    ),
                ],
            ),
        ],
        "questions": [
            (
                "What does tokenization do?",
                [
                    "Splits text into units",
                    "Encrypts a database",
                    "Creates images",
                    "Guarantees fairness",
                ],
                0,
            ),
            (
                "What does bag-of-words usually discard?",
                ["Word counts", "Word order", "Vocabulary", "Document identity"],
                1,
            ),
            (
                "Why inspect prediction errors?",
                [
                    "To hide mistakes",
                    "To understand failure patterns",
                    "To avoid evaluation",
                    "To guarantee perfection",
                ],
                1,
            ),
        ],
    },
    {
        "title": "Data Mining Fundamentals",
        "category": "Data Science",
        "art": "data-mining",
        "level": "beginner",
        "hours": 6,
        "short": "Discover the patterns hiding in plain sight. Start exploring your data.",
        "description": "Discover the basics of pattern finding in structured data. Learn about association rules, clustering, anomalies, and careful interpretation.\n\nA small market-basket assignment connects the concepts to an understandable example. No advanced mathematics is required; comfort with tables is helpful.",
        "modules": [
            (
                "Discover useful structure",
                [
                    (
                        "What makes a pattern useful?",
                        "A pattern should answer a question, occur reliably, and be relevant to a decision. Patterns found in one sample may reflect chance or collection bias.\n\nPractice: explain why a frequent purchase pair might be useful to a shop and what evidence is still missing.",
                    ),
                    (
                        "Prepare data for discovery",
                        "Check units, duplicate records, missing values, and unusual entries. Normalize identifiers consistently and preserve the original dataset so transformations can be reviewed.\n\nPractice: list cleaning rules for a basket dataset with order ID, product, and quantity.",
                    ),
                    (
                        "Support and confidence",
                        "For an association rule A implies B, support is the share of baskets containing both A and B. Confidence is the share containing B among baskets containing A. Neither metric establishes causation.\n\nPractice: if 4 of 10 baskets contain bread and milk, and 5 contain bread, calculate support and confidence.",
                    ),
                ],
            ),
            (
                "Interpret what you find",
                [
                    (
                        "Lift and meaningful associations",
                        "Lift compares a rule's confidence with the overall frequency of its consequent. A common product can give high confidence without a distinctive association. Small samples can make estimates unstable.\n\nPractice: if confidence is 0.8 and milk appears in half of baskets, calculate lift and explain it.",
                    ),
                    (
                        "Clustering and similarity",
                        "Clustering groups records according to a chosen similarity measure. Feature scaling and the number of groups affect the result. A cluster is a mathematical grouping, not automatically a real-world category.\n\nPractice: describe why income and age need careful scaling before distance-based clustering.",
                    ),
                    (
                        "Find anomalies, ask questions",
                        "An unusual record might be an error, a rare valid event, or a signal worth investigating. Review anomalies with domain context before removing them or taking action.\n\nPractice: write a short report for an unusually large order, including two plausible explanations.",
                    ),
                ],
            ),
        ],
        "questions": [
            (
                "What does support measure?",
                ["Frequency of an itemset", "A password length", "Server uptime", "A chart height"],
                0,
            ),
            (
                "Does association prove causation?",
                ["Yes", "No", "Only above 50%", "Only in SQLite"],
                1,
            ),
            (
                "An anomaly should first be…",
                [
                    "Deleted automatically",
                    "Investigated in context",
                    "Hidden",
                    "Relabeled as normal",
                ],
                1,
            ),
        ],
    },
    {
        "title": "Artificial Intelligence Basics",
        "category": "Artificial Intelligence",
        "art": "ai",
        "level": "beginner",
        "hours": 5,
        "short": "Meet the ideas behind intelligent systems. Think clearly about what's possible.",
        "description": "Build a grounded understanding of AI by exploring search, learning, evaluation, and responsible system design. Separate capabilities from assumptions and learn to ask useful questions about a system.\n\nThe final assignment proposes an assistant for a narrow educational task, with clear boundaries and a human-review plan. No programming background is required.",
        "modules": [
            (
                "Ideas behind intelligent systems",
                [
                    (
                        "AI, machine learning, and deep learning",
                        "AI is a broad field of systems performing tasks associated with intelligence. Machine learning learns patterns from data; deep learning is a family of machine learning methods using layered neural networks.\n\nPractice: draw the relationship between the three terms and give a narrow example for each.",
                    ),
                    (
                        "Search and problem solving",
                        "A search problem has states, actions, and a goal. Algorithms explore possible paths; a heuristic estimates which direction may be promising. Quality depends on the problem representation and available resources.\n\nPractice: model a small maze with states, legal moves, and a goal.",
                    ),
                    (
                        "Learning from examples",
                        "A learning system uses examples to adjust behavior. Training data, objectives, and evaluation shape what it can do. Strong performance on a benchmark does not guarantee reliability in every setting.\n\nPractice: identify how an educational assistant's input might differ from its training examples.",
                    ),
                ],
            ),
            (
                "Build with responsibility",
                [
                    (
                        "Evaluate capabilities and limits",
                        "Define a specific task and test representative cases. Include difficult and unexpected inputs. Record the kinds of errors a system makes and how those errors affect its users.\n\nPractice: create a checklist for evaluating an assistant that suggests study plans.",
                    ),
                    (
                        "Bias, privacy, and human review",
                        "AI systems can reflect biases in data or objectives. Minimize sensitive data, evaluate across relevant user groups, and define when a person must review an output.\n\nPractice: identify one bias risk and a concrete review step for a study-planning assistant.",
                    ),
                    (
                        "Design a useful bounded assistant",
                        "Start with a narrow goal, explicit inputs, and a clear way for users to correct mistakes. Provide uncertainty where appropriate and avoid using generated claims as verified facts.\n\nPractice: write a one-page proposal including users, scope, evaluation, limitations, and human oversight.",
                    ),
                ],
            ),
        ],
        "questions": [
            (
                "Machine learning is…",
                ["A subset of AI", "A database engine", "Always perfect", "A CSS framework"],
                0,
            ),
            (
                "Why test unexpected inputs?",
                [
                    "To find failure modes",
                    "To guarantee no errors",
                    "To remove human review",
                    "To avoid metrics",
                ],
                0,
            ),
            (
                "A useful AI project should begin with…",
                [
                    "An unlimited promise",
                    "A narrow, clear task",
                    "A secret dataset",
                    "No evaluation",
                ],
                1,
            ),
        ],
    },
]


class Command(BaseCommand):
    help = "Populate realistic, idempotent local demo data (DEBUG mode only)."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Demo accounts cannot be seeded with DEBUG=False. Use a local development database."
            )
        specs = [
            ("admin", "Ali", "Adil", "admin", "Admin123!"),
            ("instructor1", "Alex", "Morgan", "instructor", "Instructor123!"),
            ("instructor2", "Jamie", "Lee", "instructor", "Instructor123!"),
        ]
        names = [
            ("Sam", "Rivera"),
            ("Maya", "Chen"),
            ("Jordan", "Taylor"),
            ("Noah", "Patel"),
            ("Ava", "Williams"),
        ]
        specs += [
            (f"student{i}", first, last, "student", "Student123!")
            for i, (first, last) in enumerate(names, 1)
        ]
        users = {}
        for username, first, last, role, password in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                    "is_staff": role == "admin",
                    "is_superuser": role == "admin",
                },
            )
            if created:
                user.set_password(password)
                user.save()
                user.profile.headline = (
                    "Python educator & lifelong learner"
                    if role == "instructor"
                    else "A curious mind, one lesson at a time"
                )
                user.profile.bio = "Exploring code, data, and new possibilities. This profile is part of the Luma portfolio demonstration."
                user.profile.save()
            elif user.role != role:
                raise CommandError(
                    f"Existing username {username!r} has a different role. No changes were applied."
                )
            users[username] = user
        categories = {}
        for name, icon, description in CATALOG:
            categories[name], _ = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name, "icon": icon, "description": description},
            )
        courses = []
        for index, spec in enumerate(COURSES):
            course, _ = Course.objects.get_or_create(
                slug=slugify(spec["title"]),
                defaults={
                    "title": spec["title"],
                    "instructor": users[f"instructor{index % 2 + 1}"],
                    "category": categories[spec["category"]],
                    "short_description": spec["short"],
                    "description": spec["description"],
                    "artwork": spec["art"],
                    "difficulty": spec["level"],
                    "duration": spec["hours"],
                    "is_published": True,
                    "is_featured": index in (0, 1, 3),
                },
            )
            courses.append(course)
            for module_index, (module_title, lessons) in enumerate(spec["modules"], 1):
                module, _ = Module.objects.get_or_create(
                    course=course,
                    title=module_title,
                    defaults={
                        "order": module_index,
                        "description": "Build understanding through practical, focused lessons.",
                    },
                )
                for lesson_index, (title, content) in enumerate(lessons, 1):
                    Lesson.objects.get_or_create(
                        module=module,
                        title=title,
                        defaults={
                            "content": content,
                            "order": lesson_index,
                            "duration": 12 + lesson_index * 3,
                        },
                    )
            project_titles = [
                "Build a personal habit tracker",
                "Create an owner-scoped reading list",
                "Design a small notes application",
                "Compare a baseline and a classifier",
                "Tell a story with learning data",
                "Design a sentiment experiment",
                "Explore a market basket",
                "Propose a bounded study assistant",
            ]
            assignment, _ = Assignment.objects.get_or_create(
                course=course,
                title=project_titles[index],
                defaults={
                    "description": f"Apply the ideas from {course.title}.\n\nCreate a small project or written design that demonstrates the key concepts. Explain your approach, provide two concrete examples, and describe one limitation. For code projects, include a short sample of the core logic in your submission text.\n\nSubmit a 300–600 word reflection or a PDF/Markdown write-up. Assessment: understanding (40 marks), practical application (40 marks), and clear communication (20 marks).",
                    "due_date": timezone.now() + timedelta(days=7 + index * 3),
                    "maximum_marks": 100,
                },
            )
            quiz, _ = Quiz.objects.get_or_create(
                course=course,
                title=f"{course.title.split(' ')[0]} knowledge check",
                defaults={
                    "description": "Three focused questions to connect the ideas you've learned.",
                    "passing_percentage": 65,
                },
            )
            for order, (text, choices, correct) in enumerate(spec["questions"], 1):
                question, _ = Question.objects.get_or_create(
                    quiz=quiz, text=text, defaults={"marks": 2, "order": order}
                )
                for choice_index, choice_text in enumerate(choices):
                    Choice.objects.get_or_create(
                        question=question,
                        text=choice_text,
                        defaults={"is_correct": choice_index == correct},
                    )
            Announcement.objects.get_or_create(
                course=course,
                title="A small step for this week",
                defaults={
                    "content": "Welcome to your next chapter. Try the first module, practice its exercises, and use the knowledge check to see what clicks. Your assignment is ready when you are."
                },
            )
            for student_index in range(1, 6):
                if student_index == 1 and index not in (0, 1, 3, 4):
                    continue
                student = users[f"student{student_index}"]
                Enrollment.objects.get_or_create(student=student, course=course)
                lessons = list(Lesson.objects.filter(module__course=course))
                completed_count = (
                    [4, 2, 0, 1, 3, 1, 2, 1][index]
                    if student_index == 1
                    else (student_index + index) % 7
                )
                for lesson in lessons[:completed_count]:
                    LessonProgress.objects.get_or_create(student=student, lesson=lesson)
                Review.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        "rating": 5 if (index + student_index) % 3 else 4,
                        "text": [
                            "The examples made difficult ideas feel approachable. I built something useful after the first module.",
                            "I love being able to learn at my own pace. Seeing my progress helps me keep going.",
                            "Clear lessons and practical exercises gave me the confidence to try my own project.",
                        ][student_index % 3],
                    },
                )
                if student_index in (2, 3) or (student_index == 1 and index == 0):
                    Submission.objects.get_or_create(
                        student=student,
                        assignment=assignment,
                        defaults={
                            "text": "I connected the course ideas in a small practice project. My first example handles a normal input, and my second checks a boundary case. I separated the main logic from presentation to make the result easier to test.\n\nOne limitation is the small set of examples; a useful next step is to collect more representative cases and review the assumptions.",
                            "marks": 88 if student_index == 1 else None,
                            "feedback": "A thoughtful first project. Expand your boundary cases and explain each design decision."
                            if student_index == 1
                            else "",
                            "graded_at": timezone.now() if student_index == 1 else None,
                        },
                    )
                if (
                    completed_count >= 2
                    and not QuizAttempt.objects.filter(
                        student=student, quiz=quiz, submitted_at__isnull=False
                    ).exists()
                ):
                    attempt = QuizAttempt.objects.create(
                        student=student,
                        quiz=quiz,
                        submitted_at=timezone.now(),
                        maximum_score=6,
                        score=6 if student_index % 2 else 4,
                        passing_percentage=quiz.passing_percentage,
                    )
                    for position, question in enumerate(quiz.questions.all()):
                        correct_answer = not (student_index % 2 == 0 and position == 2)
                        choice = question.choices.filter(is_correct=correct_answer).first()
                        QuizAnswer.objects.create(
                            attempt=attempt,
                            question=question,
                            choice=choice,
                            question_text=question.text,
                            choice_text=choice.text,
                            is_correct=correct_answer,
                            awarded_marks=2 if correct_answer else 0,
                        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready: {User.objects.count()} users, {Category.objects.count()} categories, {Course.objects.count()} courses, {Lesson.objects.count()} lessons. Existing records and passwords preserved."
            )
        )
        self.stdout.write(
            "Local development only: admin / Admin123! · instructor1 / Instructor123! · student1 / Student123!"
        )
