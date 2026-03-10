import os
import json
from flask import Flask, render_template_string, request, redirect, url_for
from github import Github
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# 1. 환경 변수에서 설정 로드
# -----------------------------
# 로컬 테스트 시에는 터미널에 export GITHUB_TOKEN=... 를 입력하거나
# 아래 default 값을 임시로 수정하세요.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("REPO_NAME", "yun82kyu/my-board")

if not GITHUB_TOKEN:
    print("⚠️ 경고: GITHUB_TOKEN 환경 변수가 설정되지 않았습니다.")

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# -----------------------------
# 2. GitHub JSON 처리 함수
# -----------------------------
def load_json(file_path):
    try:
        content = repo.get_contents(file_path)
        return json.loads(content.decoded_content.decode("utf-8")), content.sha
    except Exception as e:
        print(f"로드 실패 ({file_path}): {e}")
        return [], None

def save_json(file_path, data):
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    try:
        _, sha = load_json(file_path)
        if sha:
            repo.update_file(file_path, f"Update {file_path}", json_string, sha)
        else:
            repo.create_file(file_path, f"Create {file_path}", json_string)
    except Exception as e:
        print(f"저장 실패: {e}")

# -----------------------------
# 3. HTML 레이아웃 (Summernote 포함)
# -----------------------------
HTML_LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LLM Study Board</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/summernote/0.8.18/summernote.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/summernote/0.8.18/summernote.js"></script>
    <style>
        body { padding-top: 70px; background-color: #f8f9fa; }
        .panel-body img { max-width: 100% !important; height: auto !important; display: block; margin: 10px 0; }
        .note-editable { background-color: white !important; }
    </style>
</head>
<body>
<nav class="navbar navbar-inverse navbar-fixed-top">
  <div class="container">
    <div class="navbar-header">
      <a class="navbar-brand" href="/">📚 LLM Board</a>
    </div>
    <div id="navbar" class="collapse navbar-collapse">
      <ul class="nav navbar-nav">
        {% for cat in categories %}
        <li class="{{ 'active' if current_cat == cat }}"><a href="/?cat={{ cat }}">{{ cat }}</a></li>
        {% endfor %}
      </ul>
      <ul class="nav navbar-nav navbar-right">
        <li><a href="/write" style="color: #5cb85c;"><b>[새 글 작성]</b></a></li>
      </ul>
    </div>
  </div>
</nav>

<div class="container">
    {% if mode == 'list' %}
        <div class="page-header">
          <h1>{{ current_cat }} <small>강의 노트 목록</small></h1>
        </div>
        <div class="list-group">
            {% for p in posts if p.category == current_cat %}
            <a href="/view/{{ p.no }}" class="list-group-item">
                <span class="badge">{{ p.date }}</span>
                <h4 class="list-group-item-heading">{{ p.title }}</h4>
            </a>
            {% endfor %}
            {% if not posts %} <p class="text-center">등록된 글이 없습니다.</p> {% endif %}
        </div>

    {% elif mode == 'view' %}
        <div class="panel panel-default">
            <div class="panel-heading">
                <h2 class="panel-title" style="font-size: 24px;">{{ post.title }}</h2>
            </div>
            <div class="panel-body">
                {{ post.content | safe }}
            </div>
            <div class="panel-footer text-right">
                📅 {{ post.date }} | 📂 {{ post.category }} | <a href="/">목록으로</a>
            </div>
        </div>

    {% elif mode == 'write' %}
        <div class="panel panel-primary">
            <div class="panel-heading"><h3 class="panel-title">글쓰기</h3></div>
            <div class="panel-body">
                <form action="/save" method="post">
                    <div class="form-group">
                        <label>제목</label>
                        <input type="text" name="title" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label>카테고리</label>
                        <select name="category" class="form-control">
                            {% for cat in categories %}<option>{{ cat }}</option>{% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>내용 (이미지는 복사/붙여넣기 하세요)</label>
                        <textarea id="summernote" name="content"></textarea>
                    </div>
                    <button type="submit" class="btn btn-success btn-block">저장 완료</button>
                    <a href="/" class="btn btn-default btn-block">취소</a>
                </form>
            </div>
        </div>
        <script>
            $(document).ready(function() {
                $('#summernote').summernote({
                    height: 400,
                    lang: 'ko-KR',
                    placeholder: '여기에 강의 내용을 작성하세요. 코드는 [Code View] 버튼을 활용하면 좋습니다.'
                });
            });
        </script>
    {% endif %}
</div>
</body>
</html>
"""

# -----------------------------
# 4. 라우팅 (비즈니스 로직)
# -----------------------------
@app.route('/')
def index():
    categories, _ = load_json("categories.json")
    posts, _ = load_json("data.json")
    current_cat = request.args.get('cat', categories[0] if categories else "전체")
    return render_template_string(HTML_LAYOUT, mode='list', categories=categories, posts=posts, current_cat=current_cat)

@app.route('/view/<int:no>')
def view(no):
    categories, _ = load_json("categories.json")
    posts, _ = load_json("data.json")
    post = next((p for p in posts if p['no'] == no), None)
    return render_template_string(HTML_LAYOUT, mode='view', post=post, categories=categories)

@app.route('/write')
def write():
    categories, _ = load_json("categories.json")
    return render_template_string(HTML_LAYOUT, mode='write', categories=categories)

@app.route('/save', methods=['POST'])
def save():
    posts, _ = load_json("data.json")
    new_no = max([p.get("no", 0) for p in posts], default=0) + 1
    new_post = {
        "no": new_no,
        "title": request.form.get('title'),
        "category": request.form.get('category'),
        "content": request.form.get('content'), # HTML + Base64 Image
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    posts.insert(0, new_post)
    save_json("data.json", posts)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # 로컬 테스트용 (debug=True)
    app.run(debug=True, port=5000)
