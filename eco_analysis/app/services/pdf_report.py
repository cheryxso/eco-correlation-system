from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

GREEN = HexColor('#2c5f2e')
LIGHT_GREEN = HexColor('#f0f7f0')
GRAY = HexColor('#f9f9f9')
RED_LIGHT = HexColor('#ffe0e0')
YELLOW_LIGHT = HexColor('#fff8e1')
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))

INDICATOR_LABELS = {
    'turbidity': 'Якість води',
    'PM2.5': 'PM2.5',
    'PM10': 'PM10',
    'AQI': 'Індекс якості повітря',
    'temperature': 'Температура',
    'humidity': 'Вологість',
    'pressure': 'Тиск',
    'gdp': 'ВРП',
    'salary': 'Зарплата',
    'unemployment': 'Безробіття',
    'enterprises': 'Підприємства',
    'healthcare': 'Охорона здоров’я',
    'investments': 'Інвестиції',
    'intercept': 'Константа'
}


def label(value):
    return INDICATOR_LABELS.get(value, str(value))


def val(value):
    if value is None:
        return 'N/A'
    if isinstance(value, float):
        return str(round(value, 4))
    return str(value)


def p(text, style):
    return Paragraph(str(text).replace('\n', '<br/>'), style)


def table_style(header_color=GREEN):
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ])


def add_error_block(story, title, error, heading_style, normal_style):
    story.append(Paragraph(title, heading_style))
    data = [[p('Статус', normal_style), p(error, normal_style)]]
    t = Table(data, colWidths=[4 * cm, 12 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), YELLOW_LIGHT),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(t)


def generate_pdf(
    territory_name: str,
    eco_indicator: str,
    econ_indicator: str,
    n_observations: int,
    correlation_results: dict,
    output_path: str,
    regression_result: dict = None,
    timeseries_result: dict = None,
    partial_result: dict = None,
    multiple_regression_result: dict = None,
    comparison_result: dict = None
) -> bool:
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        title_style = ParagraphStyle('Title', fontSize=18, textColor=GREEN, spaceAfter=16, fontName='DejaVuSans', leading=22)
        heading_style = ParagraphStyle('Heading', fontSize=13, textColor=GREEN, spaceBefore=14, spaceAfter=8, fontName='DejaVuSans', leading=16)
        normal_style = ParagraphStyle('Normal', fontSize=9, fontName='DejaVuSans', leading=12, spaceAfter=5)
        footer_style = ParagraphStyle('Footer', fontSize=8, textColor=HexColor('#777777'), fontName='DejaVuSans', leading=10)

        story = []
        now = datetime.now().strftime('%d.%m.%Y %H:%M')

        story.append(Paragraph('PDF-звіт кореляційного аналізу', title_style))
        info_data = [
            [p('Територія', normal_style), p(territory_name, normal_style)],
            [p('Екологічний показник', normal_style), p(label(eco_indicator), normal_style)],
            [p('Економічний показник', normal_style), p(label(econ_indicator), normal_style)],
            [p('Кількість спостережень', normal_style), p(n_observations, normal_style)],
            [p('Дата генерації', normal_style), p(now, normal_style)]
        ]
        info_table = Table(info_data, colWidths=[5 * cm, 11 * cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GREEN),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        story.append(info_table)

        story.append(Paragraph('1. Кореляційний аналіз', heading_style))
        pearson = correlation_results.get('pearson', {})
        spearman = correlation_results.get('spearman', {})
        kendall = correlation_results.get('kendall', {})
        corr_data = [[p('Метод', normal_style), p('Коефіцієнт', normal_style), p('p-value', normal_style), p('Значущість', normal_style), p('Інтерпретація', normal_style)]]
        for name, result in [('Пірсон', pearson), ('Спірмен', spearman), ('Кендалл', kendall)]:
            corr_data.append([
                p(name, normal_style),
                p(val(result.get('coefficient')), normal_style),
                p(val(result.get('p_value')), normal_style),
                p('Так' if result.get('is_significant') else 'Ні', normal_style),
                p(result.get('interpretation', ''), normal_style)
            ])
        corr_table = Table(corr_data, colWidths=[2.6 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 5.9 * cm])
        corr_table.setStyle(table_style())
        story.append(corr_table)

        normality = correlation_results.get('normality_check')
        if normality:
            story.append(Spacer(1, 0.2 * cm))
            norm_data = [
                [p('Показник', normal_style), p('Результат', normal_style), p('p-value', normal_style)],
                [p('Екологічний', normal_style), p(normality.get('eco_indicator', {}).get('note', 'N/A'), normal_style), p(val(normality.get('eco_indicator', {}).get('p_value')), normal_style)],
                [p('Економічний', normal_style), p(normality.get('econ_indicator', {}).get('note', 'N/A'), normal_style), p(val(normality.get('econ_indicator', {}).get('p_value')), normal_style)],
                [p('Рекомендація', normal_style), p(normality.get('recommendation', 'N/A'), normal_style), p('', normal_style)]
            ]
            norm_table = Table(norm_data, colWidths=[3.5 * cm, 9.5 * cm, 3 * cm])
            norm_table.setStyle(table_style())
            story.append(norm_table)

        if partial_result:
            if partial_result.get('error'):
                add_error_block(story, '2. Часткова кореляція', partial_result.get('error'), heading_style, normal_style)
            else:
                story.append(Paragraph('2. Часткова кореляція', heading_style))
                partial_data = [
                    [p('Показник', normal_style), p('Значення', normal_style)],
                    [p('Контрольна змінна', normal_style), p(label(partial_result.get('controlled_variable')), normal_style)],
                    [p('Коефіцієнт', normal_style), p(val(partial_result.get('coefficient')), normal_style)],
                    [p('p-value', normal_style), p(val(partial_result.get('p_value')), normal_style)],
                    [p('Значущість', normal_style), p('Так' if partial_result.get('is_significant') else 'Ні', normal_style)],
                    [p('Інтерпретація', normal_style), p(partial_result.get('interpretation', ''), normal_style)]
                ]
                partial_table = Table(partial_data, colWidths=[5 * cm, 11 * cm])
                partial_table.setStyle(table_style())
                story.append(partial_table)

        if timeseries_result:
            if timeseries_result.get('error'):
                add_error_block(story, '3. Аналіз часових рядів', timeseries_result.get('error'), heading_style, normal_style)
            else:
                story.append(Paragraph('3. Аналіз часових рядів', heading_style))
                cross = timeseries_result.get('cross_correlation', {})
                rolling = timeseries_result.get('rolling_correlation', {})
                ts_data = [
                    [p('Метод', normal_style), p('Результат', normal_style)],
                    [p('Крос-кореляція', normal_style), p(cross.get('interpretation', 'N/A'), normal_style)],
                    [p('Оптимальний лаг', normal_style), p(val(cross.get('optimal_lag')), normal_style)],
                    [p('Коефіцієнт при оптимальному лагу', normal_style), p(val(cross.get('optimal_correlation')), normal_style)],
                    [p('Ковзна кореляція', normal_style), p(rolling.get('interpretation', 'N/A'), normal_style)],
                    [p('Середня ковзна кореляція', normal_style), p(val(rolling.get('average_correlation')), normal_style)]
                ]
                ts_table = Table(ts_data, colWidths=[5 * cm, 11 * cm])
                ts_table.setStyle(table_style())
                story.append(ts_table)

        if regression_result:
            if regression_result.get('error'):
                add_error_block(story, '4. Лінійна регресія', regression_result.get('error'), heading_style, normal_style)
            else:
                story.append(Paragraph('4. Лінійна регресія', heading_style))
                reg_data = [
                    [p('Показник', normal_style), p('Значення', normal_style)],
                    [p('Рівняння', normal_style), p(regression_result.get('equation', 'N/A'), normal_style)],
                    [p('R²', normal_style), p(val(regression_result.get('r_squared')), normal_style)],
                    [p('Скоригований R²', normal_style), p(val(regression_result.get('adj_r_squared')), normal_style)],
                    [p('F-статистика', normal_style), p(val(regression_result.get('f_statistic')), normal_style)],
                    [p('p-value', normal_style), p(val(regression_result.get('p_value')), normal_style)],
                    [p('Значущість', normal_style), p('Так' if regression_result.get('is_significant') else 'Ні', normal_style)],
                    [p('Інтерпретація', normal_style), p(regression_result.get('interpretation', ''), normal_style)]
                ]
                reg_table = Table(reg_data, colWidths=[5 * cm, 11 * cm])
                reg_table.setStyle(table_style())
                story.append(reg_table)

        if multiple_regression_result:
            if multiple_regression_result.get('error'):
                add_error_block(story, '5. Множинна регресія', multiple_regression_result.get('error'), heading_style, normal_style)
            else:
                story.append(Paragraph('5. Множинна регресія', heading_style))
                multi_data = [
                    [p('Показник', normal_style), p('Значення', normal_style)],
                    [p('R²', normal_style), p(val(multiple_regression_result.get('r_squared')), normal_style)],
                    [p('Скоригований R²', normal_style), p(val(multiple_regression_result.get('adj_r_squared')), normal_style)],
                    [p('Кількість спостережень', normal_style), p(val(multiple_regression_result.get('n_observations')), normal_style)],
                    [p('Інтерпретація', normal_style), p(multiple_regression_result.get('interpretation', ''), normal_style)]
                ]
                multi_table = Table(multi_data, colWidths=[5 * cm, 11 * cm])
                multi_table.setStyle(table_style())
                story.append(multi_table)

                coeffs = multiple_regression_result.get('coefficients', {})
                coeff_data = [[p('Змінна', normal_style), p('Коефіцієнт', normal_style)]]
                for key, value in coeffs.items():
                    coeff_data.append([p(label(key), normal_style), p(val(value), normal_style)])
                coeff_table = Table(coeff_data, colWidths=[8 * cm, 8 * cm])
                coeff_table.setStyle(table_style())
                story.append(Spacer(1, 0.2 * cm))
                story.append(coeff_table)

                vif_rows = multiple_regression_result.get('vif', [])
                if vif_rows:
                    vif_data = [[p('Екологічний показник', normal_style), p('VIF', normal_style), p('Оцінка', normal_style)]]
                    for row in vif_rows:
                        vif_data.append([
                            p(label(row.get('indicator')), normal_style),
                            p(val(row.get('vif')), normal_style),
                            p(row.get('interpretation', ''), normal_style)
                        ])
                    vif_table = Table(vif_data, colWidths=[6 * cm, 3 * cm, 7 * cm])
                    vif_table.setStyle(table_style())
                    story.append(Spacer(1, 0.2 * cm))
                    story.append(vif_table)

        if comparison_result:
            story.append(Paragraph('6. Порівняння методів', heading_style))
            summary = comparison_result.get('summary_table', {})
            comp_data = [[p('Метод', normal_style), p('Коефіцієнт', normal_style), p('p-value', normal_style), p('Значущість', normal_style), p('Інтерпретація', normal_style)]]
            for key, name in [('pearson', 'Пірсон'), ('spearman', 'Спірмен'), ('kendall', 'Кендалл')]:
                result = summary.get(key, {})
                comp_data.append([
                    p(name, normal_style),
                    p(val(result.get('coefficient')), normal_style),
                    p(val(result.get('p_value')), normal_style),
                    p('Так' if result.get('is_significant') else 'Ні', normal_style),
                    p(result.get('interpretation', ''), normal_style)
                ])
            comp_table = Table(comp_data, colWidths=[2.6 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 5.9 * cm])
            comp_table.setStyle(table_style())
            story.append(comp_table)

            agreement = comparison_result.get('agreement', {})
            story.append(Spacer(1, 0.2 * cm))
            agreement_data = [
                [p('Узгодженість методів', normal_style), p(agreement.get('level', 'N/A'), normal_style)],
                [p('Максимальна різниця', normal_style), p(val(agreement.get('max_difference')), normal_style)],
                [p('Деталі', normal_style), p(agreement.get('detail', 'N/A'), normal_style)],
                [p('Рекомендація', normal_style), p(comparison_result.get('recommendation', 'N/A'), normal_style)]
            ]
            agreement_table = Table(agreement_data, colWidths=[5 * cm, 11 * cm])
            agreement_table.setStyle(table_style())
            story.append(agreement_table)

            conflicts = comparison_result.get('conflicts', [])
            if conflicts:
                conflict_data = [[p('Тип', normal_style), p('Опис', normal_style), p('Можлива причина', normal_style)]]
                for conflict in conflicts:
                    conflict_data.append([
                        p(conflict.get('type', ''), normal_style),
                        p(conflict.get('description', ''), normal_style),
                        p(conflict.get('possible_reason', ''), normal_style)
                    ])
                conflict_table = Table(conflict_data, colWidths=[4 * cm, 6 * cm, 6 * cm])
                conflict_table.setStyle(table_style(HexColor('#8a1c1c')))
                story.append(Spacer(1, 0.2 * cm))
                story.append(conflict_table)
            else:
                story.append(Spacer(1, 0.2 * cm))
                story.append(p('Суперечностей між методами не виявлено.', normal_style))

            ranking = comparison_result.get('ranking', [])
            if ranking:
                rank_data = [[p('Місце', normal_style), p('Метод', normal_style), p('Коефіцієнт', normal_style), p('Модуль', normal_style), p('Висновок', normal_style)]]
                for row in ranking:
                    rank_data.append([
                        p(row.get('rank', ''), normal_style),
                        p(row.get('method_name', row.get('method', '')), normal_style),
                        p(val(row.get('coefficient')), normal_style),
                        p(val(row.get('abs_coefficient')), normal_style),
                        p(row.get('conclusion', ''), normal_style)
                    ])
                rank_table = Table(rank_data, colWidths=[2 * cm, 3 * cm, 3 * cm, 3 * cm, 5 * cm])
                rank_table.setStyle(table_style())
                story.append(Spacer(1, 0.2 * cm))
                story.append(rank_table)

        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph('7. Загальний висновок', heading_style))
        story.append(p(
            f'Звіт містить результати аналізу зв’язку між показниками {label(eco_indicator)} та {label(econ_indicator)} для території {territory_name}. '
            'У звіті наведено кореляційний аналіз Пірсона, Спірмена і Кендалла, часткову кореляцію, аналіз часових рядів, лінійну регресію, множинну регресію з VIF та порівняння методів.',
            normal_style
        ))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(f'Звіт згенеровано автоматично. Дата: {now}', footer_style))

        doc.build(story)
        return True
    except Exception as e:
        print(f'PDF помилка: {e}')
        return False