use std::marker::PhantomData;

use crate::runtime;

type Invariant<T> = PhantomData<fn(T) -> T>;

pub struct Identity<'id>(PhantomData<fn(&'id ()) -> &'id ()>);

pub struct Named<'id, T> {
    value: T,
    name: runtime::Name,
    identity: PhantomData<Identity<'id>>,
}

impl<T> Named<'_, T> {
    pub fn value(&self) -> &T {
        &self.value
    }
}

pub fn name<T, R>(value: T, f: impl for<'id> FnOnce(Named<'id, T>) -> R) -> R {
    f(Named {
        value,
        name: runtime::Name::fresh(),
        identity: PhantomData,
    })
}

pub fn name2<A, B, R>(
    a: A,
    b: B,
    f: impl for<'a, 'b> FnOnce(Named<'a, A>, Named<'b, B>) -> R,
) -> R {
    name(a, |a| name(b, |b| f(a, b)))
}

pub fn name3<A, B, C, R>(
    a: A,
    b: B,
    c: C,
    f: impl for<'a, 'b, 'c> FnOnce(Named<'a, A>, Named<'b, B>, Named<'c, C>) -> R,
) -> R {
    name(a, |a| name(b, |b| name(c, |c| f(a, b, c))))
}

mod sealed {
    pub trait Sealed {}
}

pub trait Subjects: sealed::Sealed {
    type Names;
    fn handles(&self) -> Vec<runtime::Name>;
}

impl sealed::Sealed for () {}

impl Subjects for () {
    type Names = ();

    fn handles(&self) -> Vec<runtime::Name> {
        Vec::new()
    }
}

impl<T> sealed::Sealed for &Named<'_, T> {}

impl<'id, T> Subjects for &Named<'id, T> {
    type Names = Identity<'id>;

    fn handles(&self) -> Vec<runtime::Name> {
        vec![self.name.clone()]
    }
}

macro_rules! tuple_subjects {
    ($($ty:ident:$idx:tt),+) => {
        impl<$($ty: Subjects),+> sealed::Sealed for ($($ty,)+) {}

        impl<$($ty: Subjects),+> Subjects for ($($ty,)+) {
            type Names = ($($ty::Names,)+);

            fn handles(&self) -> Vec<runtime::Name> {
                let mut names = Vec::new();
                $(names.extend(self.$idx.handles());)+
                names
            }
        }
    };
}

tuple_subjects!(A:0);
tuple_subjects!(A:0, B:1);
tuple_subjects!(A:0, B:1, C:2);

pub struct Prover<K> {
    inner: runtime::Prover,
    kind: PhantomData<fn(K) -> K>,
}

pub struct Verifier<K> {
    inner: runtime::Verifier,
    kind: PhantomData<fn(K) -> K>,
}

pub struct Proof<K, N> {
    inner: runtime::Proof,
    identity: Invariant<(K, N)>,
}

pub fn define_proof<K>(kind: &str) -> Result<Prover<K>, runtime::ProofError> {
    Ok(Prover {
        inner: runtime::Prover::new(kind)?,
        kind: PhantomData,
    })
}

impl<K> Prover<K> {
    pub fn prove<S: Subjects>(
        &self,
        subjects: S,
    ) -> Result<Proof<K, S::Names>, runtime::ProofError> {
        Ok(Proof {
            inner: self.inner.prove(&subjects.handles())?,
            identity: PhantomData,
        })
    }

    pub fn verifier(&self) -> Verifier<K> {
        Verifier {
            inner: self.inner.verifier(),
            kind: PhantomData,
        }
    }
}

impl<K> Verifier<K> {
    pub fn kind(&self) -> &str {
        self.inner.kind()
    }

    pub fn require<S: Subjects>(
        &self,
        proof: &Proof<K, S::Names>,
        subjects: S,
    ) -> Result<(), runtime::ProofError> {
        self.inner.require(&proof.inner, &subjects.handles())
    }
}

impl<K, N> Proof<K, N> {
    pub fn kind(&self) -> &str {
        self.inner.kind()
    }
}
