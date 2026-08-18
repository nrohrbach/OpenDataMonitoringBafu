import requests
import pandas as pd

CKAN_BASE = "https://ckan.opendata.swiss/api/3/action"
ORG = "bundesamt-fur-umwelt-bafu"


def get_all_packages():
    packages = []
    start = 0
    rows = 500
    while True:
        resp = requests.get(
            f"{CKAN_BASE}/package_search",
            params={"fq": f"organization:{ORG}", "rows": rows, "start": start},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()["result"]
        batch = result["results"]
        packages.extend(batch)
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
    print("Abrufen aller BAFU-Packages...")
    packages = get_all_packages()
    print(f"  {len(packages)} Packages gefunden.")

    pkg_rows = []
    res_rows = []

    for pkg in packages:
        name = pkg.get("name", "")

        # Package details
        resp = requests.get(
            f"{CKAN_BASE}/package_show",
            params={"id": name},
            timeout=60,
        )
        resp.raise_for_status()
        detail = resp.json().get("result", pkg)

        # Keywords
        keywords_de = ""
        tags = detail.get("keywords", {})
        if isinstance(tags, dict):
            kw_list = tags.get("de", tags.get("en", []))
            keywords_de = ",".join(kw_list)
        elif isinstance(tags, list):
            keywords_de = ",".join(t.get("name", "") for t in tags)

        # maintainer_email: direktes Feld, Fallback auf contact_points (opendata.swiss-Standard)
        maintainer_email = detail.get("maintainer_email", "")
        if not maintainer_email:
            for cp in detail.get("contact_points", []):
                email = cp.get("email", "")
                if email:
                    maintainer_email = email
                    break

        maintainer = detail.get("maintainer", "")
        if not maintainer:
            for cp in detail.get("contact_points", []):
                name_cp = cp.get("name", "")
                if name_cp:
                    maintainer = get_multilang(name_cp, "de") if isinstance(name_cp, dict) else name_cp
                    break

        pkg_rows.append({
            "package_name": name,
            "title_de": get_multilang(detail.get("title", ""), "de"),
            "maintainer": maintainer,
            "maintainer_email": maintainer_email,
            "issued": detail.get("issued", ""),
            "modified": detail.get("modified", ""),
            "license": extract_license(detail.get("license_url", "")),
            "keywords_de": keywords_de,
        })

        for resource in detail.get("resources", []):
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
