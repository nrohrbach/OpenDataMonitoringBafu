import io
import git
import pandas as pd


def extract_history(repo, filename):
    commits = list(reversed(list(repo.iter_commits("main", paths=[filename]))))
    if not commits:
        raise SystemExit(f"Keine Commits für {filename} gefunden.")
    all_rows = []
    for commit in commits:
        date = commit.committed_datetime.strftime("%Y-%m-%d")
        try:
            content = commit.tree[filename].data_stream.read()
        except KeyError:
            continue
        df = pd.read_csv(io.BytesIO(content))
        df["snapshot_date"] = date
        all_rows.append(df)
    return pd.concat(all_rows, ignore_index=True)


if __name__ == "__main__":
    repo = git.Repo(".")
    print("Extrahiere ogd_packages History...")
    extract_history(repo, "ogd_packages.csv").to_csv("ogd_packages_history.csv", index=False)
    print("Extrahiere ogd_resources History...")
    extract_history(repo, "ogd_resources.csv").to_csv("ogd_resources_history.csv", index=False)
    print("Fertig.")
