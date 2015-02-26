/*
function toggleSubMenu(div)
{
    var submenus = document.getElementsByClassName('submenu');
    for (var i = 0; i < submenus.length; i++)
    {
        if (submenus[i].id == div.id)
        {
            if (div.style.display=="block")
                div.style.display="none";
            else
                div.style.display="block";
        }
        else
        {
            submenus[i].style.display = "none";
        }
    }
}

function hideSubMenu()
{
    var submenus = document.getElementsByClassName('submenu');
    for (var i = 0; i < submenus.length; i++)
    {
        submenus[i].style.display="none";
    }
}
*/
var gems = angular.module('gems', []);

gems.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
});