# Blog ORM Practice — Implemented Queries

Extended the `blog` app with `Category` (ManyToManyField on `Post`) and
`Comments` (ForeignKey to `Post`), then ran the following against the
Django shell (`python manage.py shell`).

## Setup

```python
from blog.models import Post, Category, Comments
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.db import connection, reset_queries
```

Data created: 4 `Category` rows, 6 `Post` rows (4 published, 2 draft),
6 `Comments` rows distributed unevenly (p1: 2, p2: 1, p3: 0, p4: 0, p5: 0, p6: 3).

---

## 1. `.filter()` — basic condition

```python
Post.objects.filter(status='published')
```
Returned 4 posts. ✅

## 2. `.exclude()` — inverse of filter

```python
Post.objects.exclude(status='draft')
```
Returned the same 4 posts as query 1 — confirms `exclude` and `filter` can express the same condition from opposite directions. ✅

## 3. `__icontains` — case-insensitive substring lookup

```python
Post.objects.filter(title__icontains='Django')
```
Returned 4 posts with "Django" in the title, regardless of case. ✅

## 4. `__gte` + `order_by` — date comparison

```python
cutoff = timezone.now() - timedelta(hours=1)
Post.objects.filter(created_at__gte=cutoff).order_by('-created_at')
```
**First attempt failed** — typo `crated_at` instead of `created_at`. Django's
`FieldError` listed valid field names, which is how the typo was caught.
Corrected version ran but returned an **empty QuerySet** — the posts were
created more than an hour before this query ran, so nothing matched. This
is expected behavior, not a bug — `__gte` genuinely found nothing recent.

## 5. `__in` — value in a list

```python
Post.objects.filter(status__in=['draft', 'published'])
```
Returned all 6 posts (both statuses exist). Also tested narrowing to just
`['draft']`, which correctly returned only the 2 draft posts. ✅

*(Note: `status__in['draft', 'published']` — without `=` — raised
`NameError`, since Python read it as indexing a variable named
`status__in` rather than passing a keyword argument.)*

## 6. `.get()` and `Post.DoesNotExist`

```python
Post.objects.get(id=1)          # returns the object directly
Post.objects.get(id=1000)       # raises Post.DoesNotExist

try:
    Post.objects.get(id=999)
except Post.DoesNotExist:
    print("No post exist")
```
Confirmed `.get()` raises a specific, catchable exception per model rather
than returning `None`. ✅

## 7. Reverse FK lookup

```python
p3 = Post.objects.get(title='Python Decorators Explained')
p3.comments.all()
```
Returned an empty QuerySet — correct, since p3 has zero comments by design. ✅

## 8. Reverse M2M lookup

```python
django_cat = Category.objects.get(name='Django')
django_cat.posts.all()
```
Returned all 4 posts tagged with the "Django" category. ✅

*(Hit `AttributeError: 'QuerySet' object has no attribute 'posts'` when
`django_cat` was set via `.filter()` instead of `.get()` — `.filter()`
always returns a QuerySet, even for a single match, and only an individual
model instance has the `related_name` attribute. Switching to `.get()`
fixed it.)*

## 9. `Q` objects — OR condition

```python
Post.objects.filter(Q(status='draft') | Q(title__icontains='docker'))
```
Returned both draft posts (one of which also matched the title condition,
but appeared only once — no duplicates). ✅

## 10. `.aggregate()` — single summary value

```python
Comments.objects.aggregate(total=Count('id'))
# {'total': 6}
```
One number for the whole table. ✅

## 11. `.annotate()` — per-row computed value

```python
Post.objects.annotate(commented_count=Count('comments')).values('title', 'commented_count')
```

**Important bug caught here.** First attempt used `Count('id')`:
```python
Post.objects.annotate(commented_count=Count('id')).values('title', 'commented_count')
```
This returned `1` for every single post — clearly wrong, since p3/p4/p5
have zero comments. The reason: `Count('id')` counts each post's **own**
`id` field, which always exists exactly once per post — it has nothing to
do with comments at all. It's a silent bug: no error, just a meaningless
number.

The correct version counts through the **relation name** instead:
```python
Post.objects.annotate(commented_count=Count('comments')).values('title', 'commented_count')
```
This correctly returned p1→2, p2→1, p3→0, p4→0, p5→0, p6→3, matching the
actual comment distribution. `Count('comments')` tells Django to count rows
in the *related* `Comments` table (via the `related_name='comments'` on
the FK) grouped per post — that's what `annotate` is for.

**Takeaway**: `Count(field)` counts non-null values of `field` per group —
pass it the name of the *relation* you want counted, not an unrelated field
on the same model.

## 12. N+1 problem, then `select_related` fix

**As run**, this printed each comment's post title twice through (once
without `select_related`, once with) but **never actually measured query
counts** — so it demonstrated the *lookup* working, not the *performance
difference*. `reset_queries()` / `connection.queries` weren't called
before the loops.

To actually prove the fix, this needs to be run as:

```python
reset_queries()
comments = Comments.objects.all()
for c in comments:
    print(c.post.title)
print(len(connection.queries))   # expect 7 (1 + 6 — one query per comment's post)
```

```python
reset_queries()
comments = Comments.objects.select_related('post').all()
for c in comments:
    print(c.post.title)
print(len(connection.queries))   # expect 1 (single JOIN query)
```

**To do**: re-run this pair with `reset_queries()`/`len(connection.queries)`
included, to get the actual before/after query counts as evidence of the
N+1 fix.

---

## Bugs encountered & lessons

| Bug | Cause | Lesson |
|---|---|---|
| `FieldError: crated_at` | Typo in field name | Django lists valid field names in the error — read it |
| `NameError: status__in` | Missing `=` before `[...]` | Python parsed it as indexing, not a kwarg |
| `IndentationError` on `try:` in shell | REPL needs manually-typed indentation per line | Type 4 spaces yourself at each `...` prompt |
| `NameError: p3`/`django_cat` not defined | Shell variables don't persist across sessions | Re-fetch with `.get()` at the start of each new shell session |
| `AttributeError: 'QuerySet' object has no attribute 'posts'` | Used `.filter()` instead of `.get()` | `.filter()` always returns a QuerySet, even with 1 match; only a single instance has reverse-relation attributes |
| `annotate(Count('id'))` returning 1 for every post | Counted the post's own `id`, not related comments | Pass the **relation name** (`'comments'`) to `Count()`, not an unrelated field |