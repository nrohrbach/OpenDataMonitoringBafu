import requests
import pandas as pd

CKAN_BASE = "https://ckan.opendata.swiss/api/3/action"
ORG = "bundesamt-fur-umwelt-bafu"


def get_all_packages():
    """Lädt alle Packages inkl. Resources in einem einzigen paginierten API-Call.
    package_search gibt bei include_private=False bereits alle Resources mit zurück —
    kein separater package_show-Call pro Package nötig.
    """
    packages = []
    start = 0
    rows = 100  # kleinere Batches = stabilere Antworten bei grossen Payloads
    while True:
        resp = requests.get(
            f"{CKAN_BASE}/package_search",
            params={
                "fq": f"organization:{ORG}",
                "rows": rows,
                "start": start,
                "include_private": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()["result"]
        batch = result["results"]
        packages.extend(batch)
        print(f"  {start + len(batch)}/{result['count']} Packages geladen...")
        if start + rows >= result["count"]:
            break
        start += rows
    return packages


def extract_license(license_url):
    if not license_url:
        return ""
    return license_url.split("#")[-1] if "#" in license_url else license_url


def get_multilang(field, lang="de"):
    if isinstance(field, dict):
        return field.get(lang, field.get("en", ""))
    return field or ""


def fetch_and_write():
    print("Abrufen aller BAFU-Packages (ohne package_show-Loop)...")
    packages = get_all_packages()
    print(f"  {len(packages)} Packages gefunden.")

    pkg_rows = []
    res_rows = []

    for pkg in packages:
        name = pkg.get("name", "")

        # Keywords — direkt aus package_search-Resultat
        keywords_de = ""
        tags = pkg.get("keywords", {})
        if isinstance(tags, dict):
            kw_list = tags.get("de", tags.get("en", []))
            keywords_de = ",".join(kw_list)
        elif isinstance(tags, list):
            keywords_de = ",".join(t.get("name", "") for t in tags)

        pkg_rows.append({
            "package_name": name,
            "title_de": get_multilang(pkg.get("title", ""), "de"),
            "maintainer": pkg.get("maintainer", ""),
            "maintainer_email": pkg.get("maintainer_email", ""),
            "issued": pkg.get("issued", ""),
            "modified": pkg.get("modified", ""),
            "license": extract_license(pkg.get("license_url", "")),
            "keywords_de": keywords_de,
        })

        for resource in pkg.get("resources", []):
            url = resource.get("url", "")
            fmt = resource.get("format", "")
            res_rows.append({
                "package_name": name,
                "resource_id": resource.get("id", ""),
                "title_de": get_multilang(resource.get("title", resource.get("name", "")), "de"),
                "format": fmt,
                "url": url,
                "media_type": resource.get("media_type", ""),
                "issued": resource.get("issued", ""),
                "modified": resource.get("modified", ""),
                "license": extract_license(resource.get("license", "")),
                "has_stac": "true" if "data.geo.admin.ch/browser" in url else "false",
                "is_service": "true" if fmt == "SERVICE" else "false",
            })

    pd.DataFrame(pkg_rows).to_csv("ogd_packages.csv", index=False, mode="w")
    pd.DataFrame(res_rows).to_csv("ogd_resources.csv", index=False, mode="w")
    print(f"  {len(pkg_rows)} Packages, {len(res_rows)} Ressourcen gespeichert.")


if __name__ == "__main__":
    fetch_and_write()
