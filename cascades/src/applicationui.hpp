#ifndef APPLICATIONUI_HPP_
#define APPLICATIONUI_HPP_

#include <bb/cascades/ArrayDataModel>

#include <QByteArray>
#include <QObject>
#include <QString>
#include <QVariant>

class QNetworkAccessManager;
class QNetworkReply;
class QTimer;

class ApplicationUI : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString pageTitle READ pageTitle NOTIFY pageChanged)
    Q_PROPERTY(QString metaLine READ metaLine NOTIFY modelChanged)
    Q_PROPERTY(QString footLine READ footLine NOTIFY modelChanged)
    Q_PROPERTY(bb::cascades::ArrayDataModel *rowModel READ rowModel CONSTANT)

public:
    ApplicationUI();
    QString pageTitle() const;
    QString metaLine() const;
    QString footLine() const;
    bb::cascades::ArrayDataModel *rowModel() const;

public Q_SLOTS:
    void showPage(const QString &name);
    void refresh();

Q_SIGNALS:
    void pageChanged();
    void modelChanged();

private Q_SLOTS:
    void onFinished();

private:
    bool applyJson(const QByteArray &raw, bool fromNetwork);
    void loadFixture();
    void render();
    void appendRow(const QString &title, const QString &detail, const QString &tone);

    bb::cascades::ArrayDataModel *m_rows;
    QNetworkAccessManager *m_nam;
    QNetworkReply *m_reply;
    QTimer *m_timer;
    QVariantMap m_data;
    QString m_page;
    QString m_meta;
    QString m_foot;
    QString m_url;
};

#endif
