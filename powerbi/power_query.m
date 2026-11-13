// Strait of Hormuz Risk Intelligence - Power Query (M) Script
let
    BasePath = "C:\path\to\strait-of-hormuz-economic-risk-intelligence\data\processed\",
    Macro = Csv.Document(File.Contents(BasePath & "fact_macro_monthly.csv"), [Delimiter=",", Encoding=65001]),
    Promoted = Table.PromoteHeaders(Macro, [PromoteAllScalars=true])
in
    Promoted
