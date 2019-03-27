'use strict';

import jQuery from "jquery";
import { clone_one_more_form_set } from "./django-formsets";

jQuery(function($)
{
    const $open_answer = $('#form-questions-open-answer');
    const $answers = $('#form-questions-answers');
    const $linked_answers = $('#form-questions-linked-answers');
    const $has_open_choices = $('#form-questions-has-open-choice');

    const $open_related_fields = $('#form-questions-open-related-fields');

    $open_answer.hide();
    $answers.hide();
    $linked_answers.hide();
    $has_open_choices.hide();

    function update_form_parts_shown()
    {
        let question_type = $('#question-edit input[name=type]:checked').val();

        switch (question_type) {
            case 'OPEN':
                $answers.hide();
                $linked_answers.hide();
                $has_open_choices.hide();
                $open_answer.show();
                $open_related_fields.show();
                break;

            case 'MCQ':
                $linked_answers.hide();
                $answers.show();
                $has_open_choices.show();
                $open_related_fields.show();

                if ($('#question-edit input[name=has_open_choice]').is(':checked'))
                {
                    $open_answer.show();
                }
                else
                {
                    $open_answer.hide();
                }
                break;

            case 'LINKED':
                $answers.hide();
                $has_open_choices.hide();
                $open_answer.hide();
                $open_related_fields.hide();

                $linked_answers.show();
                break;
        }
    }

    update_form_parts_shown();

    $('#question-edit input[name=type]').on('change', update_form_parts_shown);
    $('#question-edit input[name=has_open_choice]').on('change', update_form_parts_shown);

    $('#question-edit .form-set-delete-button').on('click', function () {
        let $delete_input = $(this).find("input[type=hidden]");
        if (!$delete_input) return;

        let $parent = $(this).parent('.field.has-addons');
        let $icon_container = $(this).find("span.button");
        let $icon = $(this).find('.fas');

        let old_title = $(this).attr('title');
        $(this).attr('title', $(this).data('other-title')).data('other-title', old_title);

        let now_deleting = $delete_input.val() !== 'on';

        if (now_deleting)
        {
            $delete_input.val('on');
            $icon_container.addClass('is-warning').removeClass("is-danger");
            $icon.removeClass('fa-trash-alt').addClass('fa-undo');
        }
        else
        {
            $delete_input.val('');
            $icon_container.removeClass('is-warning').addClass("is-danger");
            $icon.addClass('fa-trash-alt').removeClass('fa-undo');
        }

        $parent.find('input').each(function(i, e)
        {
            if (now_deleting)
            {
                $(e).attr('disabled', 'disabled').addClass("has-text-danger");
            }
            else
            {
                $(e).attr('disabled', false).removeClass("has-text-danger");
            }
        });
    });

    $('.form-set-add-button').on('click', function()
    {
        return clone_one_more_form_set($(this).parents('fieldset').find('.field.has-addons:last'));
    });
});