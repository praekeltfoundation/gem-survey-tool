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

    $scope.filters = [
        {
            "field": {
                "type": "N",
                "name": "contact"
            },
            "filters": [
                {
                    "operator": "lt",
                    "value": "18"
                },
                {
                    "loperator": "or",
                    "operator": "gt",
                    "value": "12"
                }
            ]
        },
        {
            "loperator": "or",
            "field": {
                "type": "N",
                "name": "survey"
            },
            "filters": [
                {
                    "operator": "eq",
                    "value": "female"
                }
            ]
        }
    ];

    $scope.fetchFields = function fetchFields(){
        $http.get('/get_unique_keys/')
            .success(function(data){
                $scope.fields = data;
                $scope.processFilters();
            })
    };

    $scope.addFilter = function addFilter(){
        console.log('addFilter');
    };

    $scope.addFieldFilter = function addFieldFilter(){
        console.log('addFilterFields');
    };

    $scope.removeFieldFilter = function removeFieldFilter(pIndex, index){
        $scope.filters[pIndex].filters.splice(index, 1);
    };

    $scope.processFilters = function processFilters(){
        // TODO: change all the fields to be $scope.fields[x] refs
        // TODO: change all the operators to be $scope.operators[x] refs
        $scope.filters[0].field = $scope.fields[0];
    };

    $scope.fetchFields();
});