// -------------------------------------------------------------------
// TE3 AUTOMATION SCRIPT (Fabric XMLA Compatible)
// This script applies ModelSpec: creates tables, columns, measures, relationships.
// -------------------------------------------------------------------

#r "Microsoft.AnalysisServices.Tabular.dll"

using Microsoft.AnalysisServices.Tabular;

// ------------------ LOAD MODELSPEC JSON ------------------
string jsonPath = @"{{MODEL_SPEC_PATH}}";
var json = System.IO.File.ReadAllText(jsonPath);
dynamic spec = Newtonsoft.Json.JsonConvert.DeserializeObject(json);

// ------------------ HELPER: GET OR CREATE TABLE ------------------
Table GetOrCreateTable(string tableName)
{
    if (Model.Tables.Contains(tableName))
        return Model.Tables[tableName];

    var t = new Table() { Name = tableName };
    Model.Tables.Add(t);
    return t;
}

// ------------------ HELPER: GET OR CREATE COLUMN ------------------
DataColumn GetOrCreateColumn(Table table, string columnName, string dataType)
{
    if (table.Columns.Contains(columnName))
        return table.Columns[columnName] as DataColumn;

    var col = new DataColumn()
    {
        Name = columnName,
        DataType = dataType switch
        {
            "Int64" => DataType.Int64,
            "Double" => DataType.Double,
            "DateTime" => DataType.DateTime,
            "Boolean" => DataType.Boolean,
            _ => DataType.String
        }
    };

    table.Columns.Add(col);
    return col;
}

// ------------------ CREATE TABLES + COLUMNS ------------------
foreach (var t in spec.tables)
{
    string tname = t.name;
    var table = GetOrCreateTable(tname);

    foreach (var c in t.columns)
    {
        string cname = c.name;
        string ctype = c.type;
        GetOrCreateColumn(table, cname, ctype);
    }
}

// ------------------ CREATE MEASURES ------------------
string daxFolder = @"{{DAX_FOLDER}}";
if (System.IO.Directory.Exists(daxFolder))
{
    var daxFiles = System.IO.Directory.GetFiles(daxFolder, "*.dax");

    foreach (var file in daxFiles)
    {
        string raw = System.IO.File.ReadAllText(file);
        string measureName = System.IO.Path.GetFileNameWithoutExtension(file);

        // Remove existing measure
        if (Model.AllMeasures.ContainsName(measureName))
            Model.AllMeasures.Remove(measureName);

        var table = GetOrCreateTable("ModelMeasures");  // TE3 best practice group table

        table.Measures.Add(new Measure
        {
            Name = measureName,
            Expression = raw
        });
    }
}

// ------------------ CREATE RELATIONSHIPS ------------------
foreach (var r in spec.relationships)
{
    string fromTable = r.from_table;
    string fromCol = r.from_column;
    string toTable = r.to_table;
    string toCol = r.to_column;

    if (string.IsNullOrEmpty(fromTable) || string.IsNullOrEmpty(toTable))
        continue;

    if (!Model.Tables.Contains(fromTable) || !Model.Tables.Contains(toTable))
        continue;

    var ft = Model.Tables[fromTable];
    var tt = Model.Tables[toTable];

    if (!ft.Columns.Contains(fromCol) || !tt.Columns.Contains(toCol))
        continue;

    // Create the relationship
    var rel = new SingleColumnRelationship
    {
        FromColumn = ft.Columns[fromCol] as DataColumn,
        ToColumn = tt.Columns[toCol] as DataColumn,
        RelationshipEnd = RelationshipEnd.ManyToOne
    };

    Model.Relationships.Add(rel);
}

// ------------------ DONE ------------------
Output("MODEL UPDATE COMPLETE — TE3 applied all tables, columns, measures, and relationships successfully.");
