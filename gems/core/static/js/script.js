function toggleSubmenu(div)
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