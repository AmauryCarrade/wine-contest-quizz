'use strict';

import jQuery from "jquery";

export function clone_one_more_form_set(selector, prefix)
{
    if (!prefix)
    {
        prefix = jQuery(selector).data('prefix');
    }

    let new_element = jQuery(selector).clone(true);
    let $total = jQuery('#id_' + prefix + '-TOTAL_FORMS');
    let total = $total.val();

    new_element.find(':input').each(function()
    {
        let name = jQuery(this).attr('name');

        if(name)
        {
            name = name.replace('-' + (total-1) + '-', '-' + total + '-');
            let id = 'id_' + name;
            jQuery(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        }
    });

    total++;
    $total.val(total);
    console.log(prefix, total, $total);

    jQuery(selector).after(new_element);
    return false;
}
