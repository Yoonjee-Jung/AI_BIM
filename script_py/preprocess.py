# ---------------------------------------------------------------------------- #
#                                    MODULES                                   #
# ---------------------------------------------------------------------------- #
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------- #
#                                    FOLDERS                                   #
# ---------------------------------------------------------------------------- #
energy_folder = Path(r"B:/공유 드라이브/01 진행과제/(기후에너지환경부) BIM/03 수신 자료/01 43동/EHP/43동 옥탑 EHP")
flow_folder = Path(r"B:/공유 드라이브/01 진행과제/(기후에너지환경부) BIM/03 수신 자료/01 43동/EHP/43동 적산유량")

COL_NAME  =  {energy_folder:"1.5.30.AI-0", 
              flow_folder : "1.5.34.AI-0"}
# ---------------------------------------------------------------------------- #
#                                   FUNCTIONS                                  #
# ---------------------------------------------------------------------------- #

def preprocess_folder(
    folder,
    source_column,
    output_column,
    *,
    timestamp_column="TimeStamp",
    delta_column=None,
    output_suffix="processed",
):
    """폴더의 .xls 파일을 연도별 CSV로 합쳐 저장합니다.

    delta_column을 지정하면 연도별 시간순 정렬 후 output_column의
    행간 차이를 계산해 해당 열에 저장합니다. 지정하지 않으면 차이를
    계산하지 않습니다.
    """
    folder = Path(folder)
    required_columns = [timestamp_column, source_column]
    yearly_data = {}

    files = sorted(folder.glob("*.xls"))
    if not files:
        raise FileNotFoundError(f"폴더에 .xls 파일이 없습니다: {folder}")

    for file_path in files:
        df = pd.read_excel(file_path, engine="xlrd")

        missing = [column for column in required_columns if column not in df.columns]
        if missing:
            raise ValueError(f"{file_path.name}에 필요한 열이 없습니다: {missing}")

        rename_map = {source_column: output_column}
        if timestamp_column != "TimeStamp":
            rename_map[timestamp_column] = "TimeStamp"
        df = df[required_columns].copy().rename(columns=rename_map)
        df["TimeStamp"] = pd.to_datetime(df["TimeStamp"], errors="coerce")

        invalid_rows = df["TimeStamp"].isna()
        if invalid_rows.any():
            row_numbers = (df.index[invalid_rows] + 2).tolist()
            raise ValueError(
                f"{file_path.name}에서 TimeStamp를 읽지 못했습니다. "
                f"엑셀 행 번호: {row_numbers[:10]}"
            )

        for year, group in df.groupby(df["TimeStamp"].dt.year):
            yearly_data.setdefault(year, []).append(group)

    for year, dataframes in sorted(yearly_data.items()):
        result = pd.concat(dataframes, ignore_index=True)
        result = result.sort_values("TimeStamp").reset_index(drop=True)

        if delta_column is not None:
            result[delta_column] = result[output_column].diff()

        output_path = folder / f"{year}_{output_suffix}.csv"
        result.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"저장 완료: {output_path}")


# ---------------------------------------------------------------------------- #
#                                     MAIN                                     #
# ---------------------------------------------------------------------------- #
def main():

    preprocess_folder(
        folder=flow_folder,
        source_column=COL_NAME[flow_folder],
        output_column = "Cumulative Volume",
        # output_column="EHP energy [kWh]",
        # delta_column="EHP energy delta [kWh]",
        # output_suffix="EHP_kWh",
        output_suffix = "EHP_flow"
    )


if __name__ == "__main__":
    main()
