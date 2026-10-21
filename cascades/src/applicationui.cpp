#include "applicationui.hpp"

#include <bb/cascades/AbstractPane>
#include <bb/cascades/Application>
#include <bb/cascades/QmlDocument>
#include <bb/data/JsonDataAccess>

#include <QFile>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QTimer>
#include <QUrl>
#include <QVariantList>
#include <QVariantMap>

using namespace bb::cascades;

ApplicationUI::ApplicationUI()
    : QObject()
    , m_rows(new ArrayDataModel(this))
    , m_nam(new QNetworkAccessManager(this))
    , m_reply(0)
    , m_timer(new QTimer(this))
    , m_page(QLatin1String("quota"))
    , m_url(QLatin1String("http://169.254.0.2:8786/projection.json"))
{
    const QByteArray hinted = qgetenv("Q10_CONSOLE_URL");
    if (!hinted.isEmpty()) {
        m_url = QString::fromUtf8(hinted);
    }

    QmlDocument *qml = QmlDocument::create("asset:///main.qml").parent(this);
    qml->setContextProperty("app", this);
    AbstractPane *root = qml->createRootObject<AbstractPane>();
    Application::instance()->setScene(root);

    connect(m_timer, SIGNAL(timeout()), this, SLOT(refresh()));
    m_timer->start(15000);
    loadFixture();
    refresh();
}

QString ApplicationUI::pageTitle() const
{
    if (m_page == QLatin1String("tasks")) {
        return QString::fromUtf8("任务");
    }
    if (m_page == QLatin1String("ask")) {
        return QString::fromUtf8("待处理");
    }
    return QString::fromUtf8("限额");
}

QString ApplicationUI::metaLine() const
{
    return m_meta;
}

QString ApplicationUI::footLine() const
{
    return m_foot;
}

ArrayDataModel *ApplicationUI::rowModel() const
{
    return m_rows;
}

void ApplicationUI::showPage(const QString &name)
{
    if (name == m_page) {
        return;
    }
    if (name != QLatin1String("quota") && name != QLatin1String("tasks") && name != QLatin1String("ask")) {
        return;
    }
    m_page = name;
    render();
    emit pageChanged();
}

void ApplicationUI::refresh()
{
    if (m_reply) {
        return;
    }
    QNetworkRequest req;
    req.setUrl(QUrl(m_url));
    m_reply = m_nam->get(req);
    connect(m_reply, SIGNAL(finished()), this, SLOT(onFinished()));
}

void ApplicationUI::onFinished()
{
    QNetworkReply *reply = m_reply;
    m_reply = 0;
    if (!reply) {
        return;
    }
    reply->deleteLater();
    if (reply->error() != QNetworkReply::NoError) {
        if (m_data.isEmpty()) {
            loadFixture();
        } else {
            m_data["offline"] = true;
            render();
        }
        return;
    }
    applyJson(reply->readAll(), true);
}

bool ApplicationUI::applyJson(const QByteArray &raw, bool fromNetwork)
{
    bb::data::JsonDataAccess jda;
    const QVariant parsed = jda.loadFromBuffer(raw);
    if (jda.hasError() || parsed.type() != QVariant::Map) {
        return false;
    }
    const QVariantMap map = parsed.toMap();
    if (map.value(QLatin1String("schema")).toString() != QLatin1String("q10.console.projection.v1")) {
        return false;
    }
    m_data = map;
    if (!fromNetwork) {
        m_data["upstream"] = QString::fromUtf8("fixture");
    }
    render();
    return true;
}

void ApplicationUI::loadFixture()
{
    QFile file(QLatin1String("app/native/assets/projection.json"));
    if (!file.open(QIODevice::ReadOnly)) {
        m_meta = QString::fromUtf8("没有投影");
        m_foot = QString::fromUtf8("Q限额 2任务 3待处理 · 未接 Octoooo");
        emit modelChanged();
        return;
    }
    applyJson(file.readAll(), false);
}

void ApplicationUI::appendRow(const QString &title, const QString &detail, const QString &tone)
{
    QVariantMap row;
    row["title"] = title;
    row["detail"] = detail;
    row["tone"] = tone;
    m_rows->append(row);
}

void ApplicationUI::render()
{
    m_rows->clear();
    const QString freshness = m_data.value(QLatin1String("freshness")).toString();
    const QString collected = m_data.value(QLatin1String("collected_label")).toString();
    m_meta = freshness + QString::fromUtf8(" · ") + collected;
    const int waiting = m_data.value(QLatin1String("waiting")).toInt();
    const bool offline = m_data.value(QLatin1String("offline")).toBool();
    QString src = m_data.value(QLatin1String("upstream")).toString();
    if (src.isEmpty()) {
        src = QLatin1String("aindle");
    }
    if (offline) {
        src = QString::fromUtf8("离线");
    }
    const QString waitLabel = waiting > 0
        ? (QString::fromUtf8("待处理(") + QString::number(waiting) + QLatin1String(")"))
        : QString::fromUtf8("待处理");
    m_foot = QString::fromUtf8("Q限额 2任务 3") + waitLabel + QString::fromUtf8(" · ") + src
        + QString::fromUtf8(" · 未接 Octoooo");

    if (m_page == QLatin1String("tasks")) {
        const QVariantList tasks = m_data.value(QLatin1String("tasks")).toList();
        if (tasks.isEmpty()) {
            appendRow(QString::fromUtf8("没有任务"), QString(), QLatin1String("empty"));
        }
        for (int i = 0; i < tasks.size(); ++i) {
            const QVariantMap t = tasks.at(i).toMap();
            QString title = t.value(QLatin1String("state_label")).toString() + QLatin1String(" ")
                + t.value(QLatin1String("title")).toString();
            if (t.value(QLatin1String("waiting_you")).toBool()) {
                title = QString::fromUtf8("● ") + title;
            }
            const QString tone = t.value(QLatin1String("is_stale_record")).toBool()
                ? QLatin1String("old")
                : QLatin1String("row");
            appendRow(
                title,
                t.value(QLatin1String("project")).toString() + QString::fromUtf8(" · ")
                    + t.value(QLatin1String("tool")).toString(),
                tone);
        }
    } else if (m_page == QLatin1String("ask")) {
        const QVariantList attention = m_data.value(QLatin1String("attention")).toList();
        if (attention.isEmpty()) {
            appendRow(QString::fromUtf8("没有待处理"), QString::fromUtf8("请在电脑处理"), QLatin1String("empty"));
        }
        for (int i = 0; i < attention.size(); ++i) {
            const QVariantMap a = attention.at(i).toMap();
            appendRow(
                QString::fromUtf8("● ") + a.value(QLatin1String("title")).toString(),
                QString::fromUtf8("请在电脑处理 · ") + a.value(QLatin1String("tool")).toString(),
                QLatin1String("mark"));
        }
    } else {
        const QVariantList quota = m_data.value(QLatin1String("quota")).toList();
        if (quota.isEmpty()) {
            appendRow(QString::fromUtf8("没有限额条目"), QString(), QLatin1String("empty"));
        }
        for (int i = 0; i < quota.size(); ++i) {
            const QVariantMap q = quota.at(i).toMap();
            QString detail;
            const QVariantList windows = q.value(QLatin1String("windows")).toList();
            for (int j = 0; j < windows.size(); ++j) {
                const QVariantMap w = windows.at(j).toMap();
                if (!detail.isEmpty()) {
                    detail += QLatin1String("  ");
                }
                QString pct = QString::fromUtf8("—");
                if (w.contains(QLatin1String("used_pct")) && !w.value(QLatin1String("used_pct")).isNull()) {
                    pct = w.value(QLatin1String("used_pct")).toString() + QLatin1String("%");
                }
                detail += w.value(QLatin1String("label")).toString() + QLatin1String(" ") + pct;
            }
            appendRow(
                q.value(QLatin1String("tool")).toString() + QLatin1String(" ")
                    + q.value(QLatin1String("status_label")).toString(),
                detail,
                QLatin1String("row"));
        }
        const QVariantList spend = m_data.value(QLatin1String("spend")).toList();
        if (!spend.isEmpty()) {
            QString detail;
            for (int i = 0; i < spend.size(); ++i) {
                const QVariantMap s = spend.at(i).toMap();
                if (!detail.isEmpty()) {
                    detail += QLatin1String("  ");
                }
                detail += s.value(QLatin1String("tool")).toString() + QString::fromUtf8(" · ")
                    + s.value(QLatin1String("label")).toString();
            }
            appendRow(QString::fromUtf8("花费 ≠ 限额"), detail, QLatin1String("err"));
        }
    }
    emit modelChanged();
    emit pageChanged();
}
