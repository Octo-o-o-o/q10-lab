import bb.cascades 1.2

Page {
    titleBar: TitleBar {
        title: app.pageTitle
    }
    shortcuts: [
        Shortcut { key: "q"; onTriggered: app.showPage("quota") },
        Shortcut { key: "2"; onTriggered: app.showPage("tasks") },
        Shortcut { key: "e"; onTriggered: app.showPage("tasks") },
        Shortcut { key: "3"; onTriggered: app.showPage("ask") },
        Shortcut { key: "r"; onTriggered: app.showPage("ask") },
        Shortcut { key: "4"; onTriggered: app.showPage("ask") },
        Shortcut { key: "s"; onTriggered: app.showPage("ask") },
        Shortcut { key: "t"; onTriggered: app.refresh() }
    ]
    Container {
        background: Color.create("#0B101C")
        leftPadding: 22
        rightPadding: 22
        topPadding: 16
        bottomPadding: 16
        Label {
            text: app.metaLine
            multiline: true
            textStyle.color: Color.create("#9AA3AD")
            textStyle.fontSize: FontSize.Small
        }
        ListView {
            dataModel: app.rowModel
            layoutProperties: StackLayoutProperties {
                spaceQuota: 1
            }
            listItemComponents: [
                ListItemComponent {
                    type: ""
                    Container {
                        background: Color.create("#121826")
                        topPadding: 10
                        bottomPadding: 10
                        leftPadding: 12
                        rightPadding: 12
                        bottomMargin: 10
                        Label {
                            text: ListItemData.title
                            multiline: true
                            textStyle.color: Color.create("#E8EAED")
                            textStyle.fontSize: FontSize.Medium
                        }
                        Label {
                            text: ListItemData.detail
                            multiline: true
                            visible: ListItemData.detail != ""
                            textStyle.color: Color.create("#9AA3AD")
                            textStyle.fontSize: FontSize.Small
                        }
                    }
                }
            ]
        }
        Label {
            text: app.footLine
            multiline: true
            textStyle.color: Color.create("#9AA3AD")
            textStyle.fontSize: FontSize.XSmall
        }
    }
}
