var gems = angular.module('gems');

gems.controller('queryController', function($scope, $http){

    $scope.fields = [];

    $scope.operators = [
        {name: 'Less than', operator: 'lt'},
        {name: 'Less than or equal to', operator: 'lte'},
        {name: 'Greater than', operator: 'gt'},
        {name: 'Greater than or equal to', operator: 'gte'},
        {name: 'Equal to', operator: 'eq'},
        {name: 'Text contains', operator: 'co'},
        // These are not supported yet
        {name: 'Not equal to', operator: 'neq'},
        {name: 'Text does not contain', operator: 'nco'},
        {name: 'Text is exactly', operator: 'ex'},
        {name: 'Value is null', operator: 'nu'}
    ];

    $scope.fetchFields = function fetchFields(){
        $http.get('/get_unique_keys/')
            .success(function(data){
                $scope.fields = data;
            })
    };

    $scope.fetchFields();
});