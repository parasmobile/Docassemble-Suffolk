# Changelog

Since 2.14.0, the changelog details are in [GitHub's Releases](https://github.com/SuffolkLITLab/docassemble-AssemblyLine/releases);
you can see the changes introduced in each release of the project there.

Changelogs for versions before 2.14.0 are below.

## Version v2.13.0

Added
* Export to JSON button on "share" screen
* Offer the user's address as default for second, third, etc user
* New baseline questions for probate matters
* new `show_if` parameter for all `*_fields()` methods on ALIndividuals
* Added include reference to new ALToolbox InterviewStats module

Changed
* Better contrast for accessibility
* "terms" now have a dotted underline instead of solid
* Improvements to exhibit code (OCR, etc)
* `send_button_html()` is no longer displayed if the bundle has no enabled documents
* default value of `github_user` comes from configuration instead of defaulting to `suffolklitlab`
* when the key is equal to `preview`, `_preview` is appended to filenames (to generate unique filenames in tests)
* improvements to typing (mypy)

Fixed
* the default feedback form title had literal mako tags

## Version v2.11.3

* Move the "answer set" feature behind a global configuration option (opt-in)
* Accessibility improvements
* Add PDF/A support to ALDocument class

## Version v2.11.2

Incorrect reference to save session location in the new "Answer set" feature

## Version v2.11.1

Correct the priority of the new default gender for a business; it was taking priority over the gender question

## Version v2.11.0

New:

* Added "answer set" feature that is available on production forms
* Accessibility improvements
* Minor API additions to improve developer experience with ALDocument class
* `language_fields()` method
* ALDocumentUpload class

Fixed:

* businesses have a default gender of "other" (helps language methods work correctly)
* Added some missing objects for nouns created by the Weaver
* Fixed label for "fax number" field
* return proper value when `key` function called in an addendum file

Changed:
* Types are now checked for safe usage with mypy on commit

## Version v2.10.2

Fixed:
* More protection when using snapshot feature to avoid snapshotting files/file-like objects that can't be restored
* fix some bad assumptions in the `as_editable_list()` method of ALDocumentBundle. Will work with all ALDocument subclasses now, including uploaded files

## Version v2.10.1

New features:

* added `full_names` method to ALPeopleList class (always uses full middle name, not middle initial in list)

Bug fixes:

* ensure definition of `AL_ORGANIZATION_TITLE` for feedback page
* Fix issue where you are not prompted to add additional pages to the second or more exhibit with default questions

## Version v2.10.0

Add questions for `previous_addresses` and `other_addresses`
Fix preexisting bug with address methods--missing imports

## Version v2.9.0

As of AssemblyLine v2.9.0, you can now include AssemblyLine code in your interview by
referencing `docassemble.AssemblyLine:assembly_line.yml` instead of `docassemble.AssemblyLine:al_package.yml`.
The old reference is deprecated but there are no current plans to remove it.

* Bugfixes
* Added additional comments and documentation of classes and variables
* Slightly improved phrasing of some questions
* .zip file includes DOCX files (configurable)
* Better typing
* Starting using the black autoreformatter to have more consistent Python coding style
* Remove some debugging strings

## Version v2.8.0

Bug fixes:
* email template does not trigger any extra screens, making it safer to use outside of AssemblyLine interviews
* Improvements to address question + mailing address defaults to home address
* Moved the help template for user role into the subquestion part to improve readability
* new version of ALKiln
* Remove some instances of CourtFormsOnline.org and add new variables to allow this to be customized for different jurisdictions (AL_ORGANIZATION_TITLE and AL_ORGANIZATION_HOMEPAGE)
* Small cleanups in ql_baseline.yml

## Version v2.7.1

Use metadata title, not the action title in navigation bar

## Version v2.7.0

* Add form title to the navigation bar per Theory & Principle UX audit
* Limit upload size
* Misc. accessibility fixes
* Fix bug with signature screen
* Make the "courtformsonline" a variable

## Version v2.6.2

* Add "Start over" menu option
* Merge and deprecate docassemble.LanguagePack - features are now part of AL Core

## Version v2.6.1

Increased caching for some translated strings

## Version v2.6.0

* Added new short_list method on ALPeopleList, to display abbreviated list of people
* Remove some uses of question help button
* send_button_html now triggers sending separate PDFs for each bundled item. Editable checkbox still sends Word DOCX files as appropriate
* Improved bumpversion script link to changelog

## Version v2.5.0

* Use separate PDFs in send_button_html
* Remove some question help buttons, per usability feedback
* Fix bumpversion script

## Version v2.4.1

Add back in mistakenly removed AL_DEFAULT_OVERFLOW_MESSAGE

## Version v2.4.0

Allow ALDocumentBundles to set the value of auto_gather and gathered in object declaration

## Version v2.3.8

Correct usage of include_table_of_contents in ALExhibitDocument class

## Version v2.3.7

Fixed bug in name_fields

## Version v2.3.6

Make suffix an optional field to display in name_fields() method

## Version v2.3.5

Hotfix error in country attribute of address_fields() method

## Version v2.3.4

Fix #269 - make the ALExhibitDocument class idempotent

## Version v2.3.3

Sort session names in Fast Forward (dev only feature)

## Version v2.3.1

Safer string handling in send_button_html

## Version v2.3.0

Add the ability for a developer to snapshot and fastforward sessions. This adds a HUD along with the question id

## Version v2.2.1

Important data leakage fix (#263)

## Version v2.2.0

* Added ALExhibitDocument class
* Added automated tests
* Improvements to handling of refreshed document state
* Improvements to docstrings

## v2.1.4
* Added ALStaticDocument class
* Respect filename provided on download screens
* Make submit buttons minimum of 8em wide
* Added appeals_court placeholder question

## v2.1.2
Added internationalization support to address fields methods, together with new constants `AL_DEFAULT_COUNTRY`, `AL_DEFAULT_STATE`, and `AL_DEFAULT_LANGUAGE` (use ISO 2 letter codes for all 3 parameters).

## v2.0.18

The first tagged release of Assembly Line

## v2.0.0

The first version of Assembly Line. Started at version 2, since this is a continuation of [MAVirtualCourt](https://github.com/SuffolkLITLab/MAVirtualCourt).
