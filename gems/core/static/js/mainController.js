var gems = angular.module('gems');

gems.controller('mainController', function($scope, $http, $window){
    $scope.showSurveyDataMenu = false;
    $scope.showContactMenu = false;
    $scope.showCreateGroup = false;
    $scope.showContactGroups = false;

    $scope.filters = [];
    $scope.createGroup = true;

    $scope.toggleSurveyDataMenu = function toggleSurveyDataMenu(){
        $scope.showSurveyDataMenu = !$scope.showSurveyDataMenu;

        if($scope.showSurveyDataMenu == true){
            $scope.showContactMenu = false;
        }
    };

    $scope.toggleContactMenu = function toggleContactMenu(){
        $scope.showContactMenu = !$scope.showContactMenu;

        if($scope.showContactMenu == true){
            $scope.showSurveyDataMenu = false;
        }
    };

    $scope.hideSubMenus = function hideSubMenus(url){
        $scope.showContactMenu = false;
        $scope.showSurveyDataMenu = false;
        $scope.showCreateGroup = false;
        $scope.showContactGroups = false;

        if(typeof(url) != 'undefined'){
            $window.location.href = url;
        }
    };

    $scope.showCreateContact = function showCreateContact(){
        $scope.showContactGroups = false;
        $scope.showCreateGroup = true;
        $scope.createGroup = true;
        $scope.filters = [];
    };

    $scope.hideCreateContact = function hideCreateContact(){
        $scope.showCreateGroup = false;
        $scope.filters = [];
    };

    $scope.showViewContactGroups = function showViewContactGroups(){
        $scope.showContactGroups = true;
        $scope.showCreateGroup = false;
    };

    $scope.hideViewContactGroups = function hideViewContactGroups(){
        $scope.showContactGroups = false;
    };
});
