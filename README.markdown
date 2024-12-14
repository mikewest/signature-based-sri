Explainer: Signature-based Integrity

TL;DR: It would be nice if web developers could verify the provenance of resources they depend
upon, establishing the technical foundations upon which they can increase confidence in the
integrity of their dependencies. We offer brittle, content-based integrity mechanisms today
which can (in theory) but do not (in practice) enable this capability. This proposal explores
an alternative.

## The Problem

Users rely on web developers to build sites and applications that enable everything from simple
information sharing to rich interactive experiences. Web developers often do so by composing
multiple subcomponents from a number of sources, building upon others' work and services. This
is a fantastic model in general, but it requires a level of trust in all of the dependencies that
a given site might grow to require, and certainty that only those trusted components are allowed
to execute in a given site's context. It would be unfortunate indeed if an attacker could sneak
their code into a high-value site, creating harmful consequences for developers and users both.

The web platform offers developers a few tools which provide more-or-less fine-grained control
over script execution in order to impose technical boundaries that can prevent some forms of
attack:

*   [Subresource Integrity][SRI] (SRI) allows developers to ensure that a script will execute only
    if it contains known-good content. For example, the user agent ensures that script loaded via
    "`<script src='whatever.js' integrity='sha256-...'>`" will only execute when there's an exact
    match between a SHA-256 hash of the script's content and the requirement set by the specified
    integrity attribute.

*   [Content Security Policy][CSP] (CSP) provides URL-based confinement via [host-source][]
    expressions allowing developers to restrict themselves to known-good sources. For example,
    the policy "`script-src https://example.com/script/trusted.js`" ensures that script executes
    only when it's loaded from the specified URL.

    CSP also [integrates with SRI][external] to give developers the ability to make content-based
    assertions about executable content on a page-wide basis. The policy "`script-src 'sha256-...'`"
    will allow scripts to execute from any origin, so long as they're loaded with the integrity
    checks that SRI makes possible.
 
These existing mechanisms are effective, but they also turn out to be somewhat onerous for both
development and deployment. Policies that restrict sources of content need to be quite granular in
order to meaningfully mitigate attacks, which makes robust policies difficult to deploy at scale
(see "[CSP Is Dead, Long Live CSP! On the Insecurity of Whitelists and the Future of Content
Security Policy][csp-is-dead] for more on this point). Hash-based solutions, on the other hand,
are brittle, requiring both pages and their dependencies to update in lockstep to avoid breakage.
This is possible in some deployments, but ~impossible in others where HTTP responses might be quite
dynamic.

It would be ideal if we had more options.

## The proposal

We've discussed [mixing signatures into SRI][gh-449] on and off for quite some time. Signatures are
different in kind than hashes, providing the ability to make assertions about a resource's
provenance, but not its content. This kind of guarantee can similarly remove the necessity to trust
intermediaries, and provides developers with a useful addition to URL-based and content-based
restrictions.

This proposal introduces signature-based integrity checks by first asking servers to begin signing
resources using a [narrow profile][profile] of [HTTP Message Signatures (RFC9421)][RFC9421] that's
verifiable by user agents. Developers who depend on those servers' resources can then begin
requiring that the user agent accept only those resources signed by a given key.

For example: a developer might wish to load `https://amazing.example/widget.js` in order to make
use of that component's functionality. Happily, `https://amazing.example/` is run by security-minded
folks who have integrated signing into their build process, so the server might respond with the
following headers:

```http
HTTP/1.1 200 OK
Accept-Ranges: none
Vary: Accept-Encoding
Content-Type: text/javascript; charset=UTF-8
Access-Control-Allow-Origin: *
Identity-Digest: sha-512=:[base64-encoded digest of `console.log("Hello, world!");`]:
Signature-Input: sig1=("identity-digest";sf); alg="Ed25519"; keyid="[base64-encoded public key]"; tag="sri"
Signature: sig1=:[base64-encoded result of Ed25519(`console.log("Hello, world!");`, [private key])]:

console.log("Hello, world!");
```

Three headers are particularly interesting here: `Identity-Digest`, `Signature-Input`, and
`Signature`. Let's look at each:

*   `Identity-Digest` is propsed in [ID.pardue-http-identity-digest][], and contains a digest
    of the response's decoded content (e.g. after gzip, brotli, etc is processed). This is the
    same content against which SRI compares any `integrity` requirements.

*   `Signature-Input` is defined in [RFC9421][], and spells out the components of the request
    and response that are to be signed, how that signature should be constructed, and, in this
    profile, also contains the public key that can be used to verify the signature. Because this
    header specifies a set of components that includes the `Identity-Digest` header, the signature
    is bound to the response content, not just the headers.

*   `Signature`, unsurprisingly, is also defined in [RFC9421][], and contains a signature over
    those specified components.

Users' agents will download `https://amazing.example/widget.js`, and perform two checks before
handing it back to the page for possible execution:

1.  The signature components specified in `Signature-Input` are reconstructed on the client into a
    form standardized in [RFC9421][], and the signature specified in the `Signature` header is
    verified over that reconstruction. If the signature doesn't validate, the resource is rejected.

2.  The digest specified in the `Integrity-Digest` header is verified to match a digest calculated
    over the decoded response body. If the digests don't match, the resource is rejected.

The resource is then handed back to the page for execution with the guarantee that all the
signatures on a resource are internally consistent. Developers can then choose to execute the
resource iff it can be verified using a specific public key, restricting themselves only to
resources with this proof of provenance:

```html
<script src="https://amazing.example/widget.js"
        crossorigin="anonymous"
        integrity="ed25519-[base64-encoded public key]"></script>
```

That's it. This seems like the simplest possible approach, and has some interesting properties:
 
*   It addresses many of the "evil third party" concerns that drove interest in hash-based SRI. If 
    some embedded third party content is compromised -- for example, a widget, or a JavaScript 
    library included from offsite -- an attacker may be able to maliciously alter source files, but
    hopefully won't be able to generate a valid signature for the injected code because they won't
    possess the relevant private key. Developers will be able to ensure that _their_ code is
    executing, even when it's delivered from a server outside their control.

*   Signatures seem simpler to deploy than a complete list of valid content hashes for a site,
    especially for teams who rely on shared libraries controlled by their colleagues. Coordinating
    on a keypair allows rapid deployment without rebuilding the world and distributing new hashes
    to all a libraries' dependencies.

*   Signatures can be layered on top of URL- or nonce-based restrictions in order to further
    mitigate the risk that unintended code is executed on a page. That is, if we provide an
    out-of-band signature requirement mechanism, developers could require that a given resource is
    both specified in an element with a valid nonce attribute, and is signed with a given key. For
    example, via two CSPs: "`script-src 'nonce-abc', script-src 'ed25519-zyx'`". Or even three, if
    you want URL-based confinement as well: "`script-src https://example.com/, script-src
    'nonce-abc', script-src 'ed25519-zyx'`".


[CSP]: https://w3c.github.io/webappsec-csp/
[host-source]: https://w3c.github.io/webappsec-csp/#grammardef-host-source
[SRI]: https://w3c.github.io/webappsec-subresource-integrity/
[require-sri-for]: https://w3c.github.io/webappsec-subresource-integrity/#require-sri-for
[external]: https://w3c.github.io/webappsec-csp/#external-hash
[csp-is-dead]: https://research.google.com/pubs/pub45542.html
[gh-449]: https://github.com/w3c/webappsec/issues/449
[profile]: https://wicg.github.io/signature-based-sri/#profile
[RFC9421]: https://www.rfc-editor.org/rfc/rfc9421
[ID.pardue-http-identity-digest]: https://lpardue.github.io/draft-pardue-http-identity-digest/draft-pardue-http-identity-digest.html

 
## FAQs.

*   **Does anyone need this? Really?**

    There's been interest in extending SRI to include signatures since its introduction.
    <https://github.com/w3c/webappsec/issues/449> captures some of the discussion, and though that
    discussion ends up going in a different direction than this proposal, it lays out some of the
    same deployment concerns with hashes that are discussed in this document (and that Google is
    coming across in internal discussions about particular, high-value internal applications).

    It seems likely that many companies are responsible for high-value applications that would
    benefit from robust protections against injection attacks, but who would also desire a less
    brittle deployment mechanism than hashes.

*   **This mechanism just validates a signature against a given public key. Wouldn't this allow an
    attacker to perform version rollback, delivering older versions of a script known to be
    vulnerable to attack?**

    Yes, it would. That's a significant step back from hashes, but a significant step forward from
    URLs.

    It would be possible to mitigate this risk by increasing the scope of the signature and the
    page's assertion to include some of the resource's metadata. For instance, you could imagine
    signing both the resource's body and it's `Date` header, and requiring resources newer than a
    given timestamp.

*   **Key management is hard. Periodic key pinning suicides show that HPKP is a risky thing to
    deploy; doesn't this just replicate that problem in a different way?**

    The key differences between HPKP and the mechanism proposed here are that HPKP (a) has
    origin-wide effect, (b) is irrevocable (as it kills a connection before the server is able to
    assert a new key), and (c) relies upon complex and unpredictable platform-/browser-specific
    behavior (e.g., a website can pin to an intermediate CA that might not be used by all relevant
    certificate verifiers). Signature-based SRI, on the other hand, is resource-specific,
    non-persistent, and not based on PKI and chain-building. If a developer loses their key,
    they can generate a new key pair, use the new private key to generate new signature for their
    resources, and deliver the new public key along with the next response. Suicide seems unlikely
    because there's no built-in persistence.

    It is, of course, possible that we'd introduce a persistent delivery mechanism from which it
    would be more difficult to recover. [Origin Policy][origin-policy] seems like a good candidate
    for that kind of footgun. We'll need to be careful as we approach the design if and when we
    decide that's an approach we'd like to take.

*   **Wouldn't it be better to reuse some concepts from web PKI? X.509? Chaining to roots? Etc?**

    Certs are an incredibly complicated ecosystem. This proposal is very small and simple. That also
    means that it's easy to reason about, easy to explain its benefits, and easy to recognize its
    failings. It paves the way for something more complicated in the future if it turns out that
    complexity is warranted.

*   **SHA2 doesn't allow for progressive processing of content.**

    That's not a question.

    But yes, it's correct. SHA2 has the benefits of being widely deployed and well understood, but
    they do impose a performance penalty insofar as they can't be evaluated until the resource is
    entirely present. This is a problem in general, but _not_ for scripts and stylesheets, which
    are already executed atomicly once the entire resource is present. So, SHA2 will fall down for
    many use cases, but it works just fine for these two very important cases, and fits into a
    toolkit with which developers are already familiar.

    We should extend SRI to support additional hash functions. When we do so, extending
    `Identity-Digest` will come along trivially.

    (For the record, Ed25519 is also not streaming-friendly, but the scheme described above allows
    us to do all the crypto verification directly after receiving the resource's headers, without
    waiting for the body. The lack of a streaming hash algorithm is the problem, not signature
    verification.)

[origin-policy]: https://wicg.github.io/origin-policy/
