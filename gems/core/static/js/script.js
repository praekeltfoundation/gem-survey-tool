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

gems.config(function($interpolateProvider, $httpProvider){
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
});

gems.controller('contentController', function ($scope, $http) {
    $scope.ContactGroups = {};

    $scope.group_id;

    $scope.setGroupId =  function setGroupId(id){
        $scope.group_id = id;
    }

    $scope.getContactGroups = function getContactGroups() {
        $http.get('/contactgroups/').
            success(function(data) {
                $scope.ContactGroups = data;
            }).
            error(function(data) {
                alert("failed to retreive data.");
            });
    };

    $scope.deleteContactGroup = function deleteContactGroup(){
        $http.post('/delete_contactgroup/', {group_id : $scope.group_id}).
            success(function(status){
                if(status  == "FAILED")
                    alert("Failed to delete.");
                $scope.getContactGroups();
            }).
            error(function(status){
                alert("Failed to delete.");
            });
    };

    $scope.createContactGroup = function createContactGroup(g_name){
        $http.post('/create_contactgroup/', {group_name : g_name}).
            success(function(status){
                alert(status);
            }).
            error(function(status){
                alert("failed"  + status);
            });
    };

    $scope.getContactGroups();
});