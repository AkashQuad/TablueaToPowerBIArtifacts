
let
    Source = Excel.Workbook(
        Web.Contents("https://netorgft1145305-my.sharepoint.com/:x:/g/personal/lathasri_uddemari_quadranttechnologies_com/IQCOe7m7L6gpQoH-bxv7bw3SAR618So90aSMAZO6X-EThRs?e=IueRIE"),
        null,
        true
    ),
    Data = Source{[Item="Sheet1",Kind="Sheet"]}[Data],
    PromotedHeaders = Table.PromoteHeaders(Data)
in
    PromotedHeaders
