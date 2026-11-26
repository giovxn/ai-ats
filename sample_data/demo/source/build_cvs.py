"""Builds the 9 demo CVs as real PDFs (selectable text), the way CV builders export them.

All people and companies are fictional. Contact details use example.com and placeholder numbers.
Layouts follow common modern CV structure: reverse-chronological, Profile / Experience /
Education / Skills, 1 to 2 pages (one long senior CV on purpose), mostly single-column, plus one
two-column sidebar design that many candidates still use.

    python3 build_cvs.py      # needs Google Chrome; writes ../cvs/NN_name.pdf
"""

import html
import subprocess
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path(__file__).resolve().parent.parent / "cvs"

BASE_CSS = """
@page { size: A4; margin: 16mm 17mm; }
* { box-sizing: border-box; }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.42; color: #1d1d1f; margin: 0; }
h1 { font-size: 22pt; font-weight: 600; margin: 0; letter-spacing: -0.01em; }
.headline { font-size: 11.5pt; color: #444; margin: 2px 0 6px; }
.contact { font-size: 9pt; color: #555; }
h2 { font-size: 9.5pt; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #333;
     border-bottom: 0.6pt solid #bbb; padding-bottom: 3px; margin: 16px 0 8px; }
.job { margin-bottom: 10px; break-inside: avoid; }
.job-head { display: flex; justify-content: space-between; gap: 12px; }
.job-title { font-weight: 600; }
.dates { color: #555; white-space: nowrap; }
.where { color: #555; font-size: 9.5pt; }
ul { margin: 4px 0 0; padding-left: 16px; }
li { margin: 2px 0; }
p { margin: 4px 0; }
.small { font-size: 9.5pt; color: #444; }
"""

SIDEBAR_CSS = """
@page { size: A4; margin: 0; }
body { display: flex; min-height: 297mm; }
aside { width: 64mm; background: #1f3b4d; color: #f2f5f7; padding: 16mm 8mm 16mm 10mm; font-size: 9pt; }
aside h2 { color: #cfe0ea; border-color: #4d6b7d; }
aside .contact { color: #f2f5f7; }
main { flex: 1; padding: 16mm 14mm 16mm 10mm; }
"""

TIMELINE_CSS = """
.job { display: grid; grid-template-columns: 36mm 1fr; gap: 0 8px; }
.job .dates { grid-column: 1; padding-top: 1px; }
.job .body { grid-column: 2; }
"""


def contact_line(person):
    return " | ".join(html.escape(x) for x in person["contact"])


def job_html(job, timeline=False):
    bullets = "".join(f"<li>{html.escape(b)}</li>" for b in job["bullets"])
    where = f'<div class="where">{html.escape(job["company"])}</div>'
    if timeline:
        return (f'<div class="job"><div class="dates">{html.escape(job["dates"])}</div><div class="body">'
                f'<div class="job-title">{html.escape(job["title"])}</div>{where}<ul>{bullets}</ul></div></div>')
    return (f'<div class="job"><div class="job-head"><span class="job-title">{html.escape(job["title"])}</span>'
            f'<span class="dates">{html.escape(job["dates"])}</span></div>{where}<ul>{bullets}</ul></div>')


def sections_html(person, keys, timeline=False):
    out = []
    for key in keys:
        if key == "profile" and person.get("profile"):
            out.append(f'<h2>Profile</h2><p>{html.escape(person["profile"])}</p>')
        elif key == "experience":
            out.append("<h2>Experience</h2>" + "".join(job_html(j, timeline) for j in person["jobs"]))
        elif key in person and person[key]:
            title = {"education": "Education", "skills": "Skills", "certifications": "Certifications",
                     "languages": "Languages", "projects": "Projects", "talks": "Talks and writing",
                     "volunteering": "Volunteering", "courses": "Courses"}[key]
            items = person[key]
            if isinstance(items, str):
                out.append(f"<h2>{title}</h2><p>{html.escape(items)}</p>")
            else:
                out.append(f"<h2>{title}</h2><ul>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ul>")
    return "".join(out)


def page(person):
    layout = person.get("layout", "classic")
    header = (f'<h1>{html.escape(person["name"])}</h1><div class="headline">{html.escape(person["headline"])}</div>'
              f'<div class="contact">{contact_line(person)}</div>')
    if layout == "sidebar":
        side = (f'<div class="contact">' + "<br>".join(html.escape(x) for x in person["contact"]) + "</div>"
                + sections_html(person, ["skills", "languages", "education", "certifications"]))
        main = (f'<h1>{html.escape(person["name"])}</h1><div class="headline">{html.escape(person["headline"])}</div>'
                + sections_html(person, ["profile", "experience", "projects"]))
        body, css = f"<aside>{side}</aside><main>{main}</main>", BASE_CSS + SIDEBAR_CSS
    else:
        order = ["profile", "experience", "projects", "education", "certifications", "skills", "courses",
                 "talks", "volunteering", "languages"]
        body = header + sections_html(person, order, timeline=layout == "timeline")
        css = BASE_CSS + (TIMELINE_CSS if layout == "timeline" else "")
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(person["name"])} CV</title><style>{css}</style></head><body>{body}</body></html>'


def contact(first, last, n):
    return [f"Dubai, UAE", f"{first.lower()}.{last.lower()}@example.com", f"+971 50 000 01{n:02d}",
            f"linkedin.com/in/example-{first.lower()}{last.lower()[0]}"]


PEOPLE = []

# 01 Strong fit with every must-have in the last 2 jobs: shortlist, no check needed.
PEOPLE.append(dict(
    file="01_Layla_Mansour_CV.pdf", name="Layla Mansour", headline="Senior Full-Stack Engineer",
    contact=contact("Layla", "Mansour", 1),
    profile="Full-stack engineer with 8 years in fintech and retail software. I own features from the PostgreSQL schema to the React screen, and I care about simple, well-tested code.",
    jobs=[
        dict(title="Senior Full-Stack Engineer", company="Raseed, Dubai (payments)", dates="Jan 2023 – Present", bullets=[
            "Lead engineer on the payouts dashboard: React and TypeScript front end, FastAPI services behind it",
            "Redesigned the PostgreSQL schema for payout batches, cutting the nightly reconciliation job from 40 to 6 minutes",
            "Moved our services to AWS ECS with Terraform and joined the payments on-call rota",
            "Introduced contract tests between the web app and the API; test coverage on payouts rose from 35% to 80%"]),
        dict(title="Software Engineer", company="Mazaya Retail Tech, Abu Dhabi", dates="Mar 2020 – Dec 2022", bullets=[
            "Built Django REST APIs and a React admin used by 300 stores",
            "Wrote the SQL reporting views the finance team used every week",
            "Mentored two graduate engineers through their first year"]),
        dict(title="Junior Developer", company="Brightline Studio, Amman", dates="Jul 2018 – Feb 2020", bullets=[
            "Built small Flask apps and internal tools for agency clients"]),
    ],
    education=["BSc Computer Science, University of Jordan, 2018"],
    certifications=["AWS Certified Developer – Associate, 2024"],
    skills="TypeScript, React, Next.js, Python, FastAPI, Django, PostgreSQL, Redis, AWS (ECS, RDS, SQS), Terraform, Docker, pytest, Playwright",
    languages="Arabic (native), English (fluent)",
))

# 02 Clearly wrong field: a fast reject with no check (it doesn't nag).
PEOPLE.append(dict(
    file="02_James_Whitfield_CV.pdf", name="James Whitfield", headline="Digital Marketing Executive",
    contact=contact("James", "Whitfield", 2),
    profile="Digital marketer moving into tech. I manage campaigns end to end and recently completed an introductory web development course.",
    jobs=[
        dict(title="Digital Marketing Executive", company="Coastline Hospitality Group, Dubai", dates="Feb 2022 – Present", bullets=[
            "Run paid social campaigns across five hotel brands with a monthly budget of AED 120,000",
            "Manage content on the group's WordPress websites",
            "Report weekly campaign results from Google Analytics to the commercial team"]),
        dict(title="Marketing Coordinator", company="Sunlit Events, Dubai", dates="Jun 2020 – Jan 2022", bullets=[
            "Coordinated email campaigns and event landing pages",
            "Managed the events calendar and supplier bookings"]),
    ],
    courses=["Introduction to Web Development (online, 8 weeks): HTML, CSS, basic JavaScript, 2025"],
    education=["BA Marketing, University of Leeds, 2020"],
    skills="Meta Ads, Google Ads, SEO, WordPress, Google Analytics, HubSpot, Canva, basic HTML and CSS",
    languages="English (native)",
))

# 03 THE HERO. A long senior CV: the last 2 jobs are frontend leadership, the Python backend and SQL
# work is in job 4 of 5 (2013–2017). A 20-second scan says "frontend manager"; the check appears.
PEOPLE.append(dict(
    file="03_Priya_Raman_CV.pdf", name="Priya Raman", headline="Engineering Manager, Web Platform", layout="timeline",
    contact=contact("Priya", "Raman", 3),
    profile="Engineering manager with 15 years in software, leading web teams that ship fast, accessible products. I still review code every day and like being close to the architecture, from the API contract to the component library.",
    jobs=[
        dict(title="Engineering Manager, Web Platform", company="Oasis Travel Group, Dubai", dates="Feb 2023 – Present", bullets=[
            "Manage seven engineers who own the booking web app and the shared design system",
            "Led the move of the booking flow to React and TypeScript, one screen at a time, without a feature freeze",
            "Cut median search page load from 3.9 s to 1.4 s with code splitting and caching on AWS CloudFront",
            "Made Playwright end-to-end tests part of every pull request; flaky tests fell from 8% to under 1%",
            "Run quarterly planning with product and design and present the web roadmap to the leadership team",
            "Hired four engineers in 2025 and set up a structured interview loop for the web team"]),
        dict(title="Lead Frontend Engineer", company="Kinetic Health, Dubai", dates="Jan 2020 – Jan 2023", bullets=[
            "Built the patient booking web app in React and TypeScript, used by 60,000 patients a month",
            "Created the component library with Storybook and Jest tests, adopted by three product teams",
            "Brought the app to WCAG 2.1 AA; accessibility complaints dropped to zero in 2022",
            "Worked with the API team to define GraphQL contracts for appointments and payments"]),
        dict(title="Senior Frontend Developer", company="Pixel & Grain Digital, Bangalore", dates="Jun 2017 – Dec 2019", bullets=[
            "Delivered 18 client web apps in React and Vue for retail and travel brands",
            "Built a reusable checkout widget embedded on 25 client websites",
            "Introduced code reviews and shared lint rules across the agency"]),
        dict(title="Backend Developer", company="Cargoline Logistics, Bangalore", dates="Jul 2013 – May 2017", bullets=[
            "Built and maintained the shipment tracking API in Python and Django REST Framework, serving 3 million requests a day",
            "Designed the PostgreSQL schema for shipments, routes and invoices and wrote the SQL reports finance used every month",
            "Moved label printing and customs paperwork to Celery background workers, cutting warehouse delays from hours to minutes",
            "Wrote pytest suites for the billing module and raised its test coverage from 20% to 85%",
            "Was on call for the API and wrote its incident runbooks"]),
        dict(title="Graduate Software Engineer", company="Infobridge Systems, Chennai", dates="Jul 2011 – Jun 2013", bullets=[
            "Maintained Java services and Oracle stored procedures for a banking client",
            "Fixed defects in the overnight batch jobs that produced customer statements"]),
    ],
    projects=[
        "Design system migration (Oasis Travel Group, 2024): planned the migration of 120 screens to one design system, wrote the migration guide and a codemod for common component changes, and finished two weeks early.",
        "Offline-first driver app prototype (Cargoline, 2016): a two-month prototype that let drivers capture proof of delivery without a signal and sync later. It became the basis of the company's mobile app.",
        "Booking widget (Pixel & Grain, 2018): an embeddable booking widget with a small loader script, so clients could add booking to their site with one line of code.",
    ],
    talks=[
        "Migrating a booking app without a feature freeze, Frontend Meetup Dubai, 2024",
        "Testing what users do, not how components work, JS community night, Abu Dhabi, 2025",
        "Monthly posts on the Oasis engineering blog about web performance and testing",
    ],
    education=["MSc Computer Science, Anna University, Chennai, 2011", "BEng Information Technology, Anna University, Chennai, 2009"],
    certifications=["AWS Certified Solutions Architect – Associate, 2024", "Professional Scrum Master I, 2021"],
    skills="Leadership: hiring, coaching, roadmap planning, technical writing. Frontend: React, TypeScript, Next.js, Vue, Storybook, accessibility (WCAG). Testing: Playwright, Jest, React Testing Library, pytest. Backend: Python, Django, Django REST Framework, Celery, Java. Data: PostgreSQL, Oracle, SQL. Cloud and tooling: AWS (CloudFront, S3, Lambda), Docker, GitHub Actions.",
    volunteering=["Mentor at a weekend coding club for secondary school students, Dubai (2023 – present)",
                  "Organiser of a monthly frontend study group (2024 – present)"],
    languages="English (fluent), Tamil (native), Hindi (conversational)",
))

# 04 Frontend-strong, but no Python anywhere: rejecting goes straight through, because there is
# nothing outside the 2 jobs to surface. The check only speaks when there's evidence.
PEOPLE.append(dict(
    file="04_Daniel_Okoro_CV.pdf", name="Daniel Okoro", headline="Frontend Engineer",
    contact=contact("Daniel", "Okoro", 4),
    profile="Frontend engineer who builds fast, accessible React apps and the Node.js APIs behind them.",
    jobs=[
        dict(title="Frontend Engineer", company="ShopNest, Dubai", dates="Jan 2023 – Present", bullets=[
            "Rebuilt the storefront in React and TypeScript; Lighthouse performance score from 52 to 94",
            "Built Node.js and Express APIs for the promotions engine on MySQL",
            "Set up Cypress end-to-end tests that run on every pull request"]),
        dict(title="Web Developer", company="Lagos Digital Works, Lagos", dates="Aug 2020 – Dec 2022", bullets=[
            "Built React dashboards for logistics clients on Firebase",
            "Turned Figma designs into a shared component library used by four teams"]),
    ],
    education=["BSc Computer Science, University of Lagos, 2020"],
    skills="React, TypeScript, Next.js, Node.js, Express, MySQL, Firebase, Tailwind CSS, Jest, Cypress, Figma",
    languages="English (native), Yoruba (native)",
))

# 05 Two-column sidebar design (common, harder to parse): a solid full-stack fit with recent evidence.
PEOPLE.append(dict(
    file="05_Sara_Al_Hashimi_CV.pdf", name="Sara Al Hashimi", headline="Full-Stack Developer", layout="sidebar",
    contact=["Abu Dhabi, UAE", "sara.alhashimi@example.com", "+971 50 000 0105", "linkedin.com/in/example-saraa", "Notice period: 1 month"],
    profile="Full-stack developer building insurance and claims software with Django and React. I enjoy turning slow, manual processes into simple tools.",
    jobs=[
        dict(title="Full-Stack Developer", company="Najm Insurance Tech, Abu Dhabi", dates="Apr 2022 – Present", bullets=[
            "Built the claims portal with Django, React and TypeScript, used by 1,200 brokers",
            "Designed PostgreSQL tables and SQL queries for claim tracking; report generation went from 2 hours to 4 minutes",
            "Deploy services to Google Cloud Run and write pytest and Jest tests for every change"]),
        dict(title="Backend Developer", company="Fawry Labs, Cairo", dates="Sep 2019 – Mar 2022", bullets=[
            "Built Flask APIs for a bill-payment app with 200,000 users",
            "Added integration tests and a CI pipeline in GitHub Actions"]),
    ],
    projects=["Open-source: maintainer of a small Django package for Arabic date formatting (400 GitHub stars)"],
    education=["BSc Computer Engineering, Cairo University, 2019"],
    certifications=["Google Cloud Associate Cloud Engineer, 2023"],
    skills=["Python", "Django", "Flask", "React", "TypeScript", "PostgreSQL", "Google Cloud", "Docker", "pytest", "Jest"],
    languages="Arabic (native), English (fluent)",
))

# 06 The right stack, written as duties: the card labels these bullets "Duty", with no outcomes.
PEOPLE.append(dict(
    file="06_Marco_Bellini_CV.pdf", name="Marco Bellini", headline="Full-Stack Developer",
    contact=contact("Marco", "Bellini", 6),
    profile="Full-stack developer with six years of experience in web applications for insurance and retail. Team player with good communication skills.",
    jobs=[
        dict(title="Full-Stack Developer", company="Covera Insurance, Dubai", dates="Jun 2023 – Present", bullets=[
            "Responsible for the development and maintenance of the policy portal",
            "Responsible for backend services written in Python with FastAPI",
            "Involved in the frontend migration to React and TypeScript",
            "Participated in code reviews and wrote unit tests for new features",
            "Worked with the DevOps team on deployments to AWS"]),
        dict(title="Web Developer", company="Marlow Retail Group, Milan", dates="Mar 2020 – May 2023", bullets=[
            "Responsible for the company's e-commerce website",
            "Involved in the development of REST APIs with Python and Django",
            "Worked with PostgreSQL databases and wrote SQL queries for reports"]),
    ],
    education=["BSc Computer Science, University of Milan, 2020"],
    skills="Python, FastAPI, Django, React, TypeScript, PostgreSQL, AWS, Git",
    languages="Italian (native), English (fluent)",
))

# 07 Career switcher: auditor turned developer, with Python in the current job. No check. Total years
# count all paid work, including accounting: an honest limitation to point out.
PEOPLE.append(dict(
    file="07_Aisha_Karimi_CV.pdf", name="Aisha Karimi", headline="Software Engineer (formerly Chartered Accountant)",
    contact=contact("Aisha", "Karimi", 7),
    profile="I spent seven years in audit before retraining as a developer. I now build finance features in Python and React, and my accounting background helps me understand what finance teams need from software.",
    jobs=[
        dict(title="Software Engineer", company="Ledgerly, Dubai", dates="May 2024 – Present", bullets=[
            "Build reconciliation features with FastAPI, React, TypeScript and PostgreSQL",
            "Wrote the bank-statement import service (CSV and MT940), now used by 1,100 businesses",
            "Deploy to AWS with GitHub Actions and write pytest tests for every endpoint"]),
        dict(title="Senior Auditor", company="Marlow & Pike Chartered Accountants, Dubai", dates="Sep 2016 – Aug 2023", bullets=[
            "Led audits of 14 trading and real-estate clients under IFRS",
            "Built Excel and VBA tools that cut audit sampling time by half"]),
    ],
    courses=["Full-Stack Web Development Bootcamp, CodeHarbour Academy, Dubai (Sep 2023 – Feb 2024, full time): JavaScript, React, Python, SQL"],
    education=["BSc Accounting and Finance, University of Manchester, 2016"],
    certifications=["ACCA (Fellow), 2019"],
    skills="Python, FastAPI, React, TypeScript, PostgreSQL, AWS, Git, Excel, VBA, IFRS",
    languages="English (native), Urdu (fluent), Arabic (basic)",
))

# 08 Must-haves are all recent; only nice-to-haves (Kubernetes, payments) sit in older jobs.
# Rejecting goes straight through: nice-to-haves never trigger the check.
PEOPLE.append(dict(
    file="08_Kenji_Watanabe_CV.pdf", name="Kenji Watanabe", headline="Software Engineer",
    contact=contact("Kenji", "Watanabe", 8),
    profile="Software engineer working across the stack in Python and TypeScript. Earlier in my career I worked on infrastructure for a payments company.",
    jobs=[
        dict(title="Software Engineer", company="Datelane, Dubai", dates="Aug 2024 – Present", bullets=[
            "Build scheduling features with FastAPI, React and TypeScript",
            "Wrote the PostgreSQL queries behind the availability calendar",
            "Write pytest and Vitest tests for every change; deploy to AWS ECS"]),
        dict(title="Software Engineer", company="Orbitly, Tokyo", dates="Mar 2022 – Jul 2024", bullets=[
            "Built internal admin tools in React with a Python backend",
            "Added integration tests to the CI pipeline for the admin API"]),
        dict(title="Platform Engineer", company="Hikari Pay, Tokyo", dates="Jan 2020 – Feb 2022", bullets=[
            "Ran the Kubernetes clusters for the card payments platform",
            "Built Helm charts and Docker images for twelve payment services"]),
        dict(title="Junior Developer", company="Hikari Pay, Tokyo", dates="Jul 2018 – Dec 2019", bullets=[
            "Fixed bugs in the merchant settlement service"]),
    ],
    education=["BSc Software Engineering, Keio University, 2018"],
    skills="Python, FastAPI, TypeScript, React, PostgreSQL, AWS, Docker, Kubernetes, Helm",
    languages="Japanese (native), English (fluent)",
))

# 09 Second buried case, short CV: mobile now, Python (Flask) and PostgreSQL only in job 3 of 3.
PEOPLE.append(dict(
    file="09_Rafael_Costa_CV.pdf", name="Rafael Costa", headline="Senior Mobile Engineer",
    contact=contact("Rafael", "Costa", 9),
    profile="Mobile and frontend engineer building consumer apps in React Native and TypeScript. Before moving to the client side I spent three years on backend services.",
    jobs=[
        dict(title="Senior Mobile Engineer", company="Ferrow Mobility, Dubai", dates="2022 – Present", bullets=[
            "Lead development of the rider app in React Native and TypeScript for iOS and Android",
            "Built the in-app payments flow with the payments team; checkout errors fell by 30%",
            "Added Detox end-to-end tests and Jest unit tests to the release pipeline",
            "Ship over-the-air updates through AWS Amplify and monitor crashes with Sentry"]),
        dict(title="Frontend Engineer", company="Lumo Health, Lisbon", dates="2019 – 2022", bullets=[
            "Built the patient booking web app in React and TypeScript",
            "Wrote unit and integration tests with React Testing Library for every new screen",
            "Deployed the web app to AWS S3 and CloudFront with GitHub Actions"]),
        dict(title="Backend Developer", company="Kestrel Software, Porto", dates="2016 – 2019", bullets=[
            "Built REST APIs in Python with Flask and SQLAlchemy for school management software",
            "Wrote the PostgreSQL migrations and reporting queries for 200 partner schools",
            "Added pytest tests and a CI pipeline for the API"]),
    ],
    education=["BSc Computer Engineering, University of Porto, 2016"],
    skills="React Native, React, TypeScript, JavaScript, Python, Flask, SQLAlchemy, PostgreSQL, AWS, Jest, Detox, GitHub Actions",
    languages="Portuguese (native), English (fluent), Spanish (conversational)",
))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for person in PEOPLE:
            src = Path(tmp) / (person["file"] + ".html")
            src.write_text(page(person), encoding="utf-8")
            target = OUT / person["file"]
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={target}", src.as_uri()], check=True, capture_output=True)
            print("wrote", target.name)


if __name__ == "__main__":
    main()
