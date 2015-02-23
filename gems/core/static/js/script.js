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

var gems = angular.module('gems', []);

gems.config(function($interpolateProvider){
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
});

gems.controller('contentController', function ($scope, $http) {
    $scope.ContactGroups = {};

    $scope.getContactGroups = function getContactGroups() {
        $http.get('/contactgroup/').
        success(function(data) {
            $scope.ContactGroups = data;
        }).
        error(function(data) {
            alert("failed to retreive data.");
        });
    };

    $scope.getContactGroups();
});

function editContactGroup(id)
{

}

function deleteContactGroup(id)
{

}