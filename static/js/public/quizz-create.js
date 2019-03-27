'use strict';

import jQuery from "jquery";

const max_labels_in_summary = 3;

jQuery(function($)
{
    const $option_card_contents = $('#quizz-create .ee-quizz-options .card .card-content');
    const $option_card_icons = $('#quizz-create .ee-quizz-options .card .card-header .icon .fas');
    const $radio_and_checkboxes = $option_card_contents.find('input[type=radio], input[type=checkbox]');
    const $selects = $option_card_contents.find('select');

    function update_radio_checkbox_card_summary()
    {
        let $card = $(this).closest('.card');
        let $summary = $card.find('.option-summary');
        let empty_value = $summary.data('empty-value');
        let $checked = $card.find('input:checked');

        if (($checked.length === 0 || $checked.first().val() === '') && empty_value)
        {
            $summary.text(empty_value);
        }
        else
        {
            let i = 0, all = $checked.length;
            let summary = [];

            $checked.each(function()
            {
                summary[i] = $(this).parent('label').text().trim();
                i += 1;
            });

            let summary_text;
            let summary_all_text = summary.join(', ');

            if (all > max_labels_in_summary)
            {
                summary_text = summary.slice(0, max_labels_in_summary - 1).join(', ') + ' ' + interpolate(
                    ngettext('and one other', 'and %s others', all - max_labels_in_summary + 1),
                    [all - max_labels_in_summary + 1]
                );
            }
            else
            {
                summary_text = summary_all_text;
            }

            $summary.text(summary_text);
            $summary.attr('title', summary_all_text);
        }
    }

    function update_select_card_summary()
    {
        let $card = $(this).closest('.card');
        let $summary = $card.find('.option-summary');
        let empty_value = $summary.data('empty-value');

        if ($(this).val() === '' && empty_value)
        {
            $summary.text(empty_value);
        }
        else
        {
            $summary.text($(this).find('option:checked').text().trim());
        }
    }

    $option_card_contents.hide();

    /* Accordion toggles */

    $('#quizz-create .card-header').on('click', function()
    {
        let $card_content = $(this).parent('.card').find('.card-content');
        let $card_icon = $(this).find('.fas');

        if ($card_content.is(':visible'))
        {
            $card_content.slideUp('fast');
            $card_icon.removeClass('fa-angle-up').addClass('fa-angle-down');
        }
        else
        {
            $option_card_contents.slideUp('fast');
            $option_card_icons.removeClass('fa-angle-up').addClass('fa-angle-down');

            $card_content.slideDown('fast');
            $card_icon.removeClass('fa-angle-down').addClass('fa-angle-up');
        }

        return false;
    });

    /* Cards summaries */

    // We force-update for each one at load time to handle cases
    // were the browser stores in cache old values (e.g. if the page
    // is refreshed), to be sure it always reflect the real values.
    $radio_and_checkboxes.each(update_radio_checkbox_card_summary);
    $selects.each(update_select_card_summary);

    // Then, of course, we update the summaries when the values change.
    $radio_and_checkboxes.on('change', update_radio_checkbox_card_summary);
    $selects.on('change', update_select_card_summary);
});
