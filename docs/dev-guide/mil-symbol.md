# Military Symbol Sensemaker

## Description
The Mil Symbol Sensemaker will enrich a `Node`'s Symbology Identification Code (SIDC) given information about the `Node` within OMS. It will take a `Node`'s `classIri` and various `Attribute`s about the `Node` and use it to create two SIDCs: MIL-STD-2525C, and MIL-STD-2525D. These two new codes will be stored as `Attribute`'s on the `Node` and the MIL-STD-2525C format will be updated in the `Node`'s `symbolIdCode` field.

## Triggering Sensemaker Execution
The Mil Symbol Sensemaker will execute when a `Node` is created, or restored in OMS, or when a related `Attribute` is created, restored, or updated.

## Initial SIDC Code
The Sensemaker will start with an initial code to enrich. It will first try to get the code from the `Node`'s `symbolIdCode` field. If that exists, it will be used as the initial code. If that value is empty the sensemaker will look at the ontology for a default SIDC for that `Node`'s `classIri`. If that particular IRI does not have a default SIDC, it will traverse the parent IRIs to find a default SIDC. When no default SIDC can be found, the sensemaker will start with a base SIDC of `10-0-0-00-0-0-00-000000-00-00` for MIL-STD-2525D and `SUZP------*****` for MIL-STD-2525C.

## Enrichment
After retrieving the initial SIDC, the sensmaker will enrich the code based on data from OMS. Values from the OMS data points are mapped to characters in the SIDC as defined in a config file within the sensemaker.

For MIL-STD-2525C, the sensemaker will enrich the following sections based on data about the `Node` in OMS.
* Affiliation
  * An `Attribute` with the Affiliation IRI will be retrieved from OMS to enrich the SIDC Standard Identity.
  * Example values include `friendly`, `hostile`, `suspect`
* Dimension
  * The `Node`'s `classIri` will be retrieved from OMS to enrich the SIDC dimension
  * Example values include `"http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"`, `"http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"`, `"http://www.ontologyrepository.com/CommonCoreOntologies/GroundVehicle"`
  * This value will only be updated when the initial code is Unknown.
* Status/Operational Condition
  * An `Attribute` with the Status IRI will be retrieved from OMS to enrich the SIDC Status or Operational Condition.
  * Example values include `present`, `damaged`, `destroyed`, `full to capacity`

For MIL-STD-2525D, the sensemaker will enrich the following sections based on data about the `Node` in OMS.
* Context
  * An `Attribute` with the Context IRIs will be retrieved from OMS to enrich the SIDC Context.
  * The particular IRI used will deteremine whether the context is `Reality`, `Exercise`, or `Simulation`
* Affiliation
  * An `Attribute` with the Affiliation IRI will be retrieved from OMS to enrich the SIDC Standard Identity.
  * Example values include `friendly`, `hostile`, `suspect`
* Symbol Set (Similar to Dimension)
  * The `Node`'s `classIri` will be retrieved from OMS to enrich the SIDC Symbol Set.
  * Example values include `"http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"`, `"http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"`, `"http://www.ontologyrepository.com/CommonCoreOntologies/GroundVehicle"`
  * This value will only be updated when the initial code is Unknown.
* Status
  * An `Attribute` with the Status IRI will be retrieved from OMS to enrich the SIDC Status.
  * Example values include `present`, `damaged`, `destroyed`, `full to capacity`


## Publishing Updates
Upon enriching the SIDC codes, the sensemaker will publish the updates to `OMSB`. If the SIDC code `Attribute`s exist on the `Node` already, they will be updated, otherwise, new `Attribute`s will be created. Also, the `Node`'s `symbolIdCode` value will be updated with the MIL-STD-2525C format Code.