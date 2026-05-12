# Troubleshooting

## GitHub rejects workflow file

Error:

```txt
refusing to allow a Personal Access Token to create or update workflow
```

Fix:

```bash
git rm .github/workflows/deploy.yml
git commit -m "Remove workflow file"
git push origin main
```

## Missing manifold directory

Error:

```txt
FileNotFoundError: data/manifolds/active_manifolds.json
```

Fix:

`runtime/manifold_registry.py` must contain:

```python
REGISTRY.parent.mkdir(parents=True, exist_ok=True)
```

## Collector TypeError: unhashable type dict

Cause:

```python
"payload": {{
```

Fix:

```python
"payload": {
```

## Targets disappear

Cause:

`latest.json` was overwritten with:

```json
{"active_events": []}
```

Fix:

Ensure `runtime/manifold_registry.py` synthesizes from:

```txt
data/manifolds/active_manifolds.json
```

## Dashboard stale after push

Actions:

1. Wait 1–3 minutes.
2. Hard refresh with `CTRL+F5`.
3. Confirm `latest.json` changed on GitHub.
4. Confirm `index.html` fetches `latest.json`.
