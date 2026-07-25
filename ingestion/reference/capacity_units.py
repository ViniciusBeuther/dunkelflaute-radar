"""
Load MaStR wind/solar unit XML (already extracted) into one flat Parquet table
Script for sporadic runs, just when an update to the solar/wind generators is required.

Usage:
    - uv run python -m ingestion.reference.capacity_units --xml-dir /{path}/{to}/Gesamtdatenexport_20260724_26.1
"""

import argparse
from pathlib import Path

import pandas as pd
from lxml import etree

OPERATIONAL_STATUS_ID = "35" # code for operating power plants

# csv with centroid coordinates for plz (zipcode), so we didn't lose 44% of energetic data
def load_plz_centroids(path: Path):
    plz_df = pd.read_csv(path, names=["plz", "lat", "lng"], header=0, dtype={"plz": str})
    plz_df["plz"] = plz_df["plz"].str.zfill(5)

    return dict(zip(plz_df["plz"], zip(plz_df["lat"], plz_df["lng"])))

# extract wind and solar panels coordinates to measure their locations and use as a parameter
# for open meteo API
def extract_records(
        xml_path: Path, 
        record_tag: str, 
        technology: str, 
        plz_centroids: dict[str, tuple[float, float]]
) -> list[dict]:
    records = []
    total = 0
    wrong_status = 0
    missing_coords = 0
    recovered_via_plz = 0
    missing_capacity = 0

    with open(xml_path, "rb") as file_handler:
        context = etree.iterparse(file_handler, events=("end",), tag=record_tag)
        for _, element in context:
            total += 1
            status = element.findtext("EinheitBetriebsstatus")
            lat_text = element.findtext("Breitengrad")
            lon_text = element.findtext("Laengengrad")
            capacity_text = element.findtext("Nettonennleistung")
            plz_text = element.findtext("Postleitzahl")

            if status != OPERATIONAL_STATUS_ID:
                wrong_status += 1

            elif not capacity_text:
                missing_capacity += 1
            
            else:
                latitude = float(lat_text) if lat_text else None
                longitude = float(lon_text) if lon_text else None
                location_source = "exact"

                if latitude is None or longitude is None:
                    missing_coords += 1
                    centroid = plz_centroids.get(plz_text.strip().zfill(5)) if plz_text else None
                    if centroid is not None:
                        latitude, longitude = centroid
                        location_source = "plz_centroid"
                        recovered_via_plz += 1
                
                if latitude is not None and longitude is not None:
                    records.append({
                    "technology": technology,
                    "latitude": latitude,
                    "longitude": longitude,
                    "capacity_mw": float(capacity_text) / 1000, # convert to MW
                    "location_source": location_source,
                })
            
            element.clear()
            
            while element.getprevious() is not None:
                del element.getparent()[0]
        
        del context
    
    print(
        f"  {xml_path.name}: total={total}, wrong_status={wrong_status}, "
        f"missing_capacity={missing_capacity}, missing_coords={missing_coords} "
        f"(of which has_plz={recovered_via_plz}), kept={len(records)}"
    )  
    return records

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, required=True)
    parser.add_argument("--plz-centroids", type=Path, default=Path("data/reference/plz_geocoord.csv"))
    parser.add_argument("--out", type=Path, default=Path("data/reference/mastr_units.parquet"))
    args = parser.parse_args()

    plz_centroids = load_plz_centroids(args.plz_centroids)

    all_records = []

    print("Parsing EinheitenWind.xml...")
    all_records += extract_records(args.xml_dir / "EinheitenWind.xml", "EinheitWind", "wind", plz_centroids)

    solar_files = sorted(args.xml_dir.glob("EinheitenSolar_*.xml"), key=lambda p: int(p.stem.split("_")[1]))
    for i, path in enumerate(solar_files, start=1):
        print(f"Parsing {path.name} ({i}/{len(solar_files)})...")
        all_records += extract_records(path, "EinheitSolar", "solar", plz_centroids)
    
    df = pd.DataFrame(all_records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    print(f"Wrote {len(df)} operational units to {args.out}")
    print(df.groupby(["technology", "location_source"])["capacity_mw"].sum())

if __name__ == "__main__":
    main()